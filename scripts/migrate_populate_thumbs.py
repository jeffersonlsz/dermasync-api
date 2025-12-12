#!/usr/bin/env python3
"""
Migration helper: varre collection 'imagens' e tenta popular fields:
  - thumb_path (string) -> caminho preferencial do thumbnail no bucket
  - paths (list[string]) -> lista de caminhos relacionados (inclui storage_path e thumb_path)

Modo seguro (default): dry-run -> apenas reporta o que faria.
Use --apply para efetivar updates.
Use --force para sobrescrever thumb_path existente.
"""

import argparse
import logging
import sys
import os
from typing import List, Optional
from datetime import datetime
import time

# Adiciona o diretório raiz do projeto ao sys.path para encontrar o pacote 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ajuste o import conforme seu projeto
from app.firestore.client import get_firestore_client, get_storage_bucket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("migrate_populate_thumbs")


# Heurísticas de candidates para thumbs (ordem importante)
THUMB_CANDIDATES_TEMPLATES = [
    "{id}/thumb_{orig}",            # thumb original naming
    "{id}/thumb_{basename}",        # thumb using basename only
    "{id}/thumbnail.jpg",
    "{id}/thumb.jpg",
    "{id}/thumb_{id}.jpg",
    "{id}/antes_{orig}",
    "{id}/depois_{orig}",
    "{id}/antes_{basename}",
    "{id}/depois_{basename}",
]

# Normaliza filename -> basename (strip dirs)
def _basename(filename: str) -> str:
    if not filename:
        return ""
    return filename.split("/")[-1].split("\\")[-1]


def find_existing_blob(bucket, path: str) -> bool:
    """
    Verifica existência de blob. Retorna True se existe.
    Usa .exists() synchronous method.
    """
    try:
        blob = bucket.blob(path)
        return blob.exists()
    except Exception as e:
        logger.exception("Erro ao checar existência do blob %s: %s", path, e)
        return False


def candidate_paths_for_item(item: dict) -> List[str]:
    """
    Dado um documento normalizado (tem 'id', 'storage_path', 'original_filename'),
    retorna lista de candidate paths a checar no bucket (strings).
    """
    idv = item.get("id") or item.get("_id") or ""
    orig = item.get("original_filename") or item.get("filename") or ""
    basename = _basename(orig)
    candidates = []
    for t in THUMB_CANDIDATES_TEMPLATES:
        candidate = t.format(id=idv, orig=orig, basename=basename)
        candidates.append(candidate)
    # também inclua storage_path's variants if present
    sp = item.get("storage_path") or ""
    if sp:
        # candidate thumb near storage_path: replace filename with thumb.jpg
        parts = sp.rsplit("/", 1)
        if len(parts) == 2:
            prefix = parts[0]
            candidates.append(f"{prefix}/thumb.jpg")
            candidates.append(f"{prefix}/thumbnail.jpg")
            candidates.append(f"{prefix}/thumb_{basename}" if basename else f"{prefix}/thumb.jpg")
    return candidates


def merge_paths(existing_paths: Optional[List[str]], new_paths: List[str]) -> List[str]:
    merged = list(existing_paths or [])
    for p in new_paths:
        if p and p not in merged:
            merged.append(p)
    return merged


def run_migration(limit: Optional[int], batch_size: int, apply: bool, force: bool):
    db = get_firestore_client()
    bucket = get_storage_bucket()
    coll = db.collection("imagens")

    logger.info("Starting migration. dry_run=%s, limit=%s, batch_size=%s, force=%s", not apply, limit, batch_size, force)

    # Stream documents (be careful with very large collections)
    docs_iter = coll.stream()
    processed = 0
    to_update = []  # list of tuples (doc_ref, payload)
    stats = {"checked": 0, "found_thumb": 0, "will_update": 0, "skipped_existing_thumb": 0}

    start_time = time.time()
    for doc in docs_iter:
        if limit is not None and processed >= limit:
            break
        data = doc.to_dict() or {}
        data["id"] = doc.id
        stats["checked"] += 1

        storage_path = data.get("storage_path") or ""
        original_filename = data.get("original_filename") or data.get("filename") or ""
        # if no storage_path, skip (can't generate signed urls later anyway)
        if not storage_path:
            logger.debug("Doc %s has no storage_path; skipping.", doc.id)
            processed += 1
            continue

        candidates = candidate_paths_for_item(data)
        found_thumb = None
        for cand in candidates:
            if not cand:
                continue
            exists = False
            try:
                exists = find_existing_blob(bucket, cand)
            except Exception:
                exists = False
            if exists:
                found_thumb = cand
                break

        if found_thumb:
            stats["found_thumb"] += 1
            existing_thumb = data.get("thumb_path")
            if existing_thumb and not force:
                logger.info("Doc %s: thumb already exists (%s). Skipping (use --force to overwrite).", doc.id, existing_thumb)
                stats["skipped_existing_thumb"] += 1
            else:
                # prepare update payload
                current_paths = data.get("paths") if isinstance(data.get("paths"), list) else []
                new_paths = merge_paths(current_paths, [storage_path, found_thumb])
                payload = {}
                if not existing_thumb or force:
                    payload["thumb_path"] = found_thumb
                payload["paths"] = new_paths
                to_update.append((doc.reference, payload))
                stats["will_update"] += 1
                logger.info("Doc %s: will set thumb_path=%s (storage_path=%s)", doc.id, found_thumb, storage_path)
        else:
            logger.debug("Doc %s: no thumb candidate found. Consider generating thumbnails for id=%s", doc.id, doc.id)

        processed += 1

        # Apply in batches if apply==True
        if apply and len(to_update) >= batch_size:
            logger.info("Applying batch of %d updates...", len(to_update))
            batch = db.batch()
            for ref, payload in to_update:
                batch.update(ref, payload)
            try:
                batch.commit()
                logger.info("Batch committed.")
            except Exception as e:
                logger.exception("Error committing batch: %s", e)
            to_update = []

    # final flush
    if apply and to_update:
        logger.info("Applying final batch of %d updates...", len(to_update))
        batch = db.batch()
        for ref, payload in to_update:
            batch.update(ref, payload)
        try:
            batch.commit()
            logger.info("Final batch committed.")
        except Exception as e:
            logger.exception("Error committing final batch: %s", e)

    elapsed = time.time() - start_time
    logger.info("Migration finished. checked=%d found_thumb=%d will_update=%d skipped_existing_thumb=%d elapsed=%.1fs",
                stats["checked"], stats["found_thumb"], stats["will_update"], stats["skipped_existing_thumb"], elapsed)


def parse_args():
    p = argparse.ArgumentParser(description="Populate thumb_path and paths in Firestore imagens collection.")
    p.add_argument("--apply", action="store_true", help="Apply updates to Firestore. Default is dry-run.")
    p.add_argument("--limit", type=int, default=None, help="Limit number of documents to process (useful for testing).")
    p.add_argument("--batch-size", type=int, default=50, help="Batch size for Firestore updates.")
    p.add_argument("--force", action="store_true", help="Overwrite existing thumb_path if present.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_migration(limit=args.limit, batch_size=args.batch_size, apply=args.apply, force=args.force)
    except Exception as e:
        logger.exception("Migration failed: %s", e)
        sys.exit(1)
