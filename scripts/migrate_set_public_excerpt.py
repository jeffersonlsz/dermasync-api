from datetime import datetime, timezone
from firebase_admin import credentials, firestore, initialize_app
import os

# ================= CONFIG =================
SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "dermasync-key.json"
)

COLLECTION_NAME = "relatos"  # ajuste se necessário
DRY_RUN = False              # ⚠️ TESTE PRIMEIRO COM True
BATCH_SIZE = 400
EXCERPT_MAX_LEN = 120
# =========================================

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
initialize_app(cred)
db = firestore.client()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def extract_narrative(doc: dict) -> str | None:
    """
    Compatível com relatos legados e novos
    """
    if isinstance(doc.get("conteudo_original"), str):
        return doc["conteudo_original"]

    if isinstance(doc.get("descricao"), str):
        return doc["descricao"]

    return None


def build_public_excerpt(doc: dict) -> dict | None:
    narrative = extract_narrative(doc)

    if not narrative:
        return None

    text_excerpt = narrative.strip()[:EXCERPT_MAX_LEN]

    return {
        "public_excerpt": {
            "text": text_excerpt,
            "age_range": None,
            "duration": None,
            "tags": doc.get("tags_extraidas", []),
            "image_previews": None
        },
        "public_excerpt_created_at": now_iso()
    }


def migrate():
    print(f"\n🚀 Backfill de public_excerpt (schema-aware)")
    print(f"Coleção: {COLLECTION_NAME}")
    print(f"Dry run: {DRY_RUN}\n")

    docs = db.collection(COLLECTION_NAME).stream()

    batch = db.batch()
    batch_count = 0
    updated = 0
    skipped = 0
    failed = 0

    for snap in docs:
        data = snap.to_dict()

        if "public_excerpt" in data:
            skipped += 1
            continue

        payload = build_public_excerpt(data)

        if payload is None:
            failed += 1
            continue

        if not DRY_RUN:
            batch.update(snap.reference, payload)
            batch_count += 1

        updated += 1

        if batch_count >= BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            batch_count = 0
            print(f"✔ Commit parcial | atualizados={updated}")

    if not DRY_RUN and batch_count > 0:
        batch.commit()

    print("\n=== RESULTADO FINAL ===")
    print(f"Atualizados: {updated}")
    print(f"Ignorados (já tinham): {skipped}")
    print(f"Falharam (sem narrativa): {failed}")


if __name__ == "__main__":
    migrate()
