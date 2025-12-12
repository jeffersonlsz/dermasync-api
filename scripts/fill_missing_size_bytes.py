# scripts/fill_missing_size_bytes.py
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
# para que os módulos da 'app' possam ser encontrados.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.firestore.client import get_firestore_client, get_storage_bucket

def main():
    db = get_firestore_client()
    bucket = get_storage_bucket()
    imgs = list(db.collection("imagens").stream())

    for doc in imgs:
        data = doc.to_dict() or {}
        if not data.get("storage_path"):
            continue
        if data.get("size_bytes"):
            continue

        sp = data["storage_path"]
        blob = bucket.blob(sp)
        try:
            b = blob.download_as_bytes()
            size = len(b)
            print(f"Doc {doc.id}: size = {size}")
            db.collection("imagens").document(doc.id).update({"size_bytes": size})
        except Exception as e:
            print(f"Erro ao baixar {sp}: {e}")

if __name__ == "__main__":
    main()
