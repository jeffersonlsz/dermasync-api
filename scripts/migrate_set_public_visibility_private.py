from datetime import datetime, timezone
from firebase_admin import credentials, firestore, initialize_app
import os

# ===== CONFIG =====
SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "dermasync-key.json"  # ajuste se necessário
)

COLLECTION_NAME = "relatos"  # ou "galeria"
DRY_RUN = False  # >>> coloque True para testar sem escrever
BATCH_SIZE = 400  # Firestore limit-safe
# ==================

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
initialize_app(cred)

db = firestore.client()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def migrate():
    print(f"\n🔎 Iniciando migração em '{COLLECTION_NAME}' (dry_run={DRY_RUN})")

    docs = db.collection(COLLECTION_NAME).stream()

    batch = db.batch()
    updated = 0
    skipped = 0
    batch_count = 0

    for doc in docs:
        data = doc.to_dict()

        if "public_visibility" in data:
            skipped += 1
            continue

        update_payload = {
            "public_visibility": {
                "status": "PRIVATE",
                "reason": "legacy_migration_default",
                "updated_at": now_iso()
            }
        }

        if not DRY_RUN:
            batch.update(doc.reference, update_payload)
            batch_count += 1

        updated += 1

        if batch_count >= BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            batch_count = 0
            print(f"✔ Commit parcial ({updated} atualizados)")

    if not DRY_RUN and batch_count > 0:
        batch.commit()

    print("\n=== MIGRAÇÃO FINALIZADA ===")
    print(f"Atualizados: {updated}")
    print(f"Ignorados (já tinham campo): {skipped}")

if __name__ == "__main__":
    migrate()
