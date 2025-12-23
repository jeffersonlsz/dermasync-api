"""
Geração idempotente de thumbnails para imagens já associadas a um relato.
- NÃO cria imagens
- NÃO altera relato
- Apenas gera thumbnail se não existir
"""

from firebase_admin import credentials, firestore, storage, initialize_app
from datetime import datetime, timezone
from urllib.parse import unquote
from io import BytesIO
import requests
from PIL import Image, ImageOps
import os

# ========= CONFIG =========

RELATO_ID = "01qIN1QpujNPG4uyMJQ8"
FIREBASE_KEY_PATH = "dermasync-key.json"
THUMB_SIZE = 256
THUMB_PREFIX = "thumb_256_"

# ========= INIT =========

cred = credentials.Certificate(FIREBASE_KEY_PATH)
initialize_app(cred, {
    "storageBucket": "dermasync-3d14a.firebasestorage.app"
})

db = firestore.client()
bucket = storage.bucket()

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
    blob = bucket.blob(path)
    return blob.download_as_bytes()

def upload_to_storage(path: str, data: bytes):
    blob = bucket.blob(path)
    blob.upload_from_string(data, content_type="image/jpeg")

# ========= MAIN =========

def generate_thumbnails_for_relato(relato_id: str):
    imagens = (
        db.collection("imagens")
        .where("relato_id", "==", relato_id)
        .stream()
    )

    found = False

    for img in imagens:
        found = True
        data = img.to_dict()
        img_ref = img.reference

        storage_info = data.get("storage", {})
        original_path = storage_info.get("original_path")
        thumb_path = storage_info.get("thumb_path")

        if not original_path:
            print(f"[SKIP] imagem {img.id} sem original_path")
            continue

        if thumb_path:
            print(f"[OK] thumbnail já existe → {img.id}")
            continue

        filename = os.path.basename(original_path)
        thumb_path = f"{os.path.dirname(original_path)}/{THUMB_PREFIX}{filename}"

        print(f"[PROCESS] gerando thumbnail para {img.id}")

        try:
            original_bytes = download_from_storage(original_path)
            thumb_bytes = generate_thumbnail(original_bytes)
            upload_to_storage(thumb_path, thumb_bytes)

            img_ref.update({
                "storage.thumb_path": thumb_path,
                "timestamps.updated_at": now_iso()
            })

            print(f"[DONE] thumbnail criada → {thumb_path}")

        except Exception as e:
            print(f"[ERROR] imagem {img.id}: {e}")

    if not found:
        print("Nenhuma imagem encontrada para este relato.")

if __name__ == "__main__":
    generate_thumbnails_for_relato(RELATO_ID)
