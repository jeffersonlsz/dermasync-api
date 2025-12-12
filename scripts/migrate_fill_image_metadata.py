# scripts/migrate_fill_image_metadata.py
import sys
import os
from datetime import datetime, timezone
import io
import hashlib
from PIL import Image
import argparse

# Adiciona o diretório raiz do projeto ao sys.path
# para que os módulos da 'app' possam ser encontrados.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# reutilizar os clientes que seu app já inicializa
from app.firestore.client import get_firestore_client, get_storage_bucket

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Aplicar (por padrão dry-run).")
    return p.parse_args()

def main(apply=False):
    db = get_firestore_client()
    bucket = get_storage_bucket()

    coll = db.collection("imagens")
    docs = list(coll.stream())

    for doc in docs:
        d = doc.to_dict() or {}
        changes = {}
        sp = d.get("storage_path")
        if not sp:
            paths = d.get("paths")
            if paths and isinstance(paths, list) and len(paths) > 0:
                sp = paths[0]
                changes["storage_path"] = sp

        if sp:
            blob = bucket.blob(sp)
            try:
                exists = blob.exists()
            except Exception as e:
                print(f"[WARN] não pôde checar blob.exists() para {sp}: {e}")
                exists = False

            if exists:
                # metadata disponíveis
                try:
                    if "size_bytes" not in d:
                        changes["size_bytes"] = int(blob.size) if blob.size is not None else None
                    if "content_type" not in d and blob.content_type:
                        changes["content_type"] = blob.content_type
                except Exception as e:
                    print("Warn metadados:", e)

                # tentar baixar e extrair dimensões + sha256 (cuidado: custo/tempo)
                try:
                    data = blob.download_as_bytes()
                    img = Image.open(io.BytesIO(data))
                    if "width" not in d:
                        changes["width"] = img.width
                    if "height" not in d:
                        changes["height"] = img.height
                    if "sha256" not in d:
                        changes["sha256"] = hashlib.sha256(data).hexdigest()
                except Exception as e:
                    print(f"[WARN] não foi possível inspecionar blob {sp}: {e}")

        # normalizar created_at / updated_at
        if "created_at" not in d and "criado_em" in d:
            try:
                changes["created_at"] = datetime.fromisoformat(d["criado_em"].replace("Z", "+00:00"))
            except Exception:
                changes["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in d:
            changes["updated_at"] = changes.get("created_at", datetime.now(timezone.utc))

        if changes:
            print(f"Doc {doc.id} -> changes: {changes}")
            if apply:
                coll.document(doc.id).update(changes)
        else:
            print(f"Doc {doc.id} -> ok")

if __name__ == "__main__":
    args = get_args()
    main(apply=args.apply)
