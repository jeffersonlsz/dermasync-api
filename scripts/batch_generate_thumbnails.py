"""
Batch idempotente de geração de thumbnails para imagens no Firestore.

- NÃO cria documentos
- NÃO remove dados
- NÃO altera relatos
- Apenas gera thumbnail se storage.thumb_path estiver vazio

Flags:
--limit N
--dry-run
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from io import BytesIO

# Adiciona o diretório raiz ao path para permitir imports da 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.firestore.client import get_firestore_client
from app.adapters.firebase_storage_adapter import FirebaseStorageAdapter
from PIL import Image, ImageOps

# ========= CONFIG =========

THUMB_SIZE = 256
THUMB_PREFIX = "thumb_256_"

# ========= INIT =========

db = get_firestore_client()
storage_adapter = FirebaseStorageAdapter()

# ========= HELPERS =========

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def generate_thumbnail(image_bytes: bytes) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        img = ImageOps.exif_transpose(img)

        if img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        min_dim = min(w, h)

        left = (w - min_dim) // 2
        top = (h - min_dim) // 2

        img = img.crop((left, top, left + min_dim, top + min_dim))
        img = img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)

        buffer = BytesIO()
        img.save(
            buffer,
            format="JPEG",
            quality=85,
            optimize=True,
            progressive=True
        )
        return buffer.getvalue()

def download_from_storage(path: str) -> bytes:
    return storage_adapter._download_bytes_sync(path)

def upload_to_storage(path: str, data: bytes):
    storage_adapter._upload_bytes_sync(path=path, content=data, content_type="image/jpeg")


# ========= MAIN =========

def run_batch(limit: int | None, dry_run: bool):
    query = db.collection("imagens").where("storage.thumb_path", "==", None)

    if limit:
        query = query.limit(limit)

    docs = list(query.stream())

    if not docs:
        print("Nenhuma imagem pendente de thumbnail.")
        return

    print(f"Encontradas {len(docs)} imagens sem thumbnail.")
    if dry_run:
        print("â ï¸ DRY-RUN ATIVO: nenhuma alteração será feita.")

    processed = 0
    skipped = 0
    errors = 0

    for doc in docs:
        data = doc.to_dict()
        ref = doc.reference

        original_path = data.get("storage", {}).get("original_path")

        if not original_path:
            print(f"[SKIP] {doc.id} sem original_path")
            skipped += 1
            continue

        filename = os.path.basename(original_path)
        thumb_path = f"{os.path.dirname(original_path)}/{THUMB_PREFIX}{filename}"

        print(f"[PROCESS] {doc.id}")

        if dry_run:
            print(f"  â geraria thumbnail em {thumb_path}")
            processed += 1
            continue

        try:
            original_bytes = download_from_storage(original_path)
            thumb_bytes = generate_thumbnail(original_bytes)
            upload_to_storage(thumb_path, thumb_bytes)

            ref.update({
                "storage.thumb_path": thumb_path,
                "timestamps.updated_at": now_iso()
            })

            print(f"[DONE] thumbnail criada")
            processed += 1

        except Exception as e:
            print(f"[ERROR] {doc.id}: {e}")
            errors += 1

    print("\n===== RESUMO =====")
    print(f"Processadas: {processed}")
    print(f"Pulos:       {skipped}")
    print(f"Erros:       {errors}")

# ========= CLI =========

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limite de imagens")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    run_batch(args.limit, args.dry_run)
