"""
Batch de migração de imagens legadas em relatos.

- Converte campo legado `imagens` em documentos na collection `imagens`
- Cria `imagens_ref` no relato
- NÃO remove dados legados
- NÃO recria se já migrado

Flags:
--limit N
--dry-run
"""

import argparse
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote

from firebase_admin import credentials, firestore, initialize_app

# ========= CONFIG =========

FIREBASE_KEY_PATH = "dermasync-key.json"

# ========= INIT =========

cred = credentials.Certificate(FIREBASE_KEY_PATH)
initialize_app(cred)

db = firestore.client()

# ========= HELPERS =========

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def extract_storage_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.split("/o/")[-1]
    return unquote(path)

def create_image_doc(
    relato_id: str,
    papel_clinico: str,
    storage_path: str,
    ordem: int | None,
    dry_run: bool
):
    image_id = str(uuid.uuid4())

    doc = {
        "imagem_id": image_id,
        "relato_id": relato_id,
        "papel_clinico": papel_clinico,
        "ordem": ordem,
        "storage": {
            "original_path": storage_path,
            "thumb_path": None
        },
        "status": {
            "moderacao": "pending",
            "visibilidade": "private"
        },
        "timestamps": {
            "created_at": now_iso(),
            "updated_at": now_iso()
        },
        "versao_schema": 1
    }

    if dry_run:
        print(f"    [DRY] criaria imagem {papel_clinico} ({image_id})")
        return image_id

    db.collection("imagens").document(image_id).set(doc)
    return image_id

# ========= MAIN =========

def run_batch(limit: int | None, dry_run: bool):
    query = db.collection("relatos").where("imagens", "!=", None)

    if limit:
        query = query.limit(limit)

    relatos = list(query.stream())

    if not relatos:
        print("Nenhum relato com imagens legadas encontrado.")
        return

    print(f"Encontrados {len(relatos)} relatos candidatos.")
    if dry_run:
        print("⚠️ DRY-RUN ATIVO")

    migrated = 0
    skipped = 0
    errors = 0

    for doc in relatos:
        relato_id = doc.id
        data = doc.to_dict()
        ref = doc.reference

        print(f"\n[RELATO] {relato_id}")

        if "imagens_ref" in data:
            print("  → já migrado, pulando")
            skipped += 1
            continue

        imagens_legado = data.get("imagens")
        if not imagens_legado:
            print("  → sem imagens legadas")
            skipped += 1
            continue

        imagens_ref = {
            "antes": None,
            "depois": None,
            "durante": []
        }

        try:
            # ---- ANTES ----
            if imagens_legado.get("antes"):
                path = extract_storage_path_from_url(imagens_legado["antes"])
                imagens_ref["antes"] = create_image_doc(
                    relato_id, "ANTES", path, None, dry_run
                )

            # ---- DEPOIS ----
            if imagens_legado.get("depois"):
                path = extract_storage_path_from_url(imagens_legado["depois"])
                imagens_ref["depois"] = create_image_doc(
                    relato_id, "DEPOIS", path, None, dry_run
                )

            # ---- DURANTE ----
            for idx, url in enumerate(imagens_legado.get("durante", [])):
                path = extract_storage_path_from_url(url)
                img_id = create_image_doc(
                    relato_id, "DURANTE", path, idx, dry_run
                )
                imagens_ref["durante"].append(img_id)

            if dry_run:
                print("  [DRY] imagens_ref seria:", imagens_ref)
            else:
                ref.update({
                    "imagens_ref": imagens_ref,
                    "imagens_count": {
                        "antes": 1 if imagens_ref["antes"] else 0,
                        "depois": 1 if imagens_ref["depois"] else 0,
                        "durante": len(imagens_ref["durante"])
                    },
                    "versao_schema": data.get("versao_schema", 1) + 1,
                    "updated_at": now_iso()
                })

            migrated += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            errors += 1

    print("\n===== RESUMO =====")
    print(f"Migrados: {migrated}")
    print(f"Pulos:    {skipped}")
    print(f"Erros:    {errors}")

# ========= CLI =========

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    run_batch(args.limit, args.dry_run)
