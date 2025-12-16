from firebase_admin import credentials, firestore, initialize_app
import os

# ================= CONFIG =================
SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "dermasync-key.json"
)

COLLECTION_NAME = "relatos"  # ajuste se necessário
DRY_RUN = False              # ⚠️ rode primeiro com True
BATCH_SIZE = 400
# =========================================

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
initialize_app(cred)
db = firestore.client()


def migrate():
    print("\n🔁 Migração: criado_em → created_at")
    print(f"Coleção: {COLLECTION_NAME}")
    print(f"Dry run: {DRY_RUN}\n")

    docs = db.collection(COLLECTION_NAME).stream()

    batch = db.batch()
    batch_count = 0
    renamed = 0
    skipped = 0
    failed = 0

    for snap in docs:
        data = snap.to_dict()

        if "criado_em" not in data:
            skipped += 1
            continue

        if "created_at" in data:
            skipped += 1
            continue

        criado_em_value = data.get("criado_em")

        if criado_em_value is None:
            failed += 1
            continue

        update_payload = {
            "created_at": criado_em_value,
            "criado_em": firestore.DELETE_FIELD
        }

        if not DRY_RUN:
            batch.update(snap.reference, update_payload)
            batch_count += 1

        renamed += 1

        if batch_count >= BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            batch_count = 0
            print(f"✔ Commit parcial | renomeados={renamed}")

    if not DRY_RUN and batch_count > 0:
        batch.commit()

    print("\n=== RESULTADO FINAL ===")
    print(f"Renomeados: {renamed}")
    print(f"Ignorados: {skipped}")
    print(f"Falharam: {failed}")


if __name__ == "__main__":
    migrate()
