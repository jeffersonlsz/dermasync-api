# scripts/migracao/2026_02_add_id_field_relato.py

import sys
from typing import List
import os
# Adiciona o diretório raiz do projeto ao sys.path
# para que os módulos da 'app' possam ser encontrados.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
from app.firestore.client import get_firestore_client


COLLECTION_NAME = "relatos"
DRY_RUN = False  # ð´ TROQUE PARA False PARA EXECUTAR DE VERDADE
BATCH_LIMIT = 400


def migrar_ids():
    db = get_firestore_client()
    collection = db.collection(COLLECTION_NAME)

    docs = collection.stream()

    batch = db.batch()
    count_batch = 0
    total_updated = 0
    total_skipped = 0

    for doc in docs:
        doc_id = doc.id
        data = doc.to_dict()

        if "id" in data:
            print(f"[SKIP] {doc_id} já possui campo id.")
            total_skipped += 1
            continue

        print(f"[UPDATE] {doc_id} -> adicionando campo id")

        if not DRY_RUN:
            batch.update(doc.reference, {"id": doc_id})
            count_batch += 1

        total_updated += 1

        if count_batch == BATCH_LIMIT:
            batch.commit()
            batch = db.batch()
            count_batch = 0

    if not DRY_RUN and count_batch > 0:
        batch.commit()

    print("\n===== RESULTADO =====")
    print(f"Atualizados: {total_updated}")
    print(f"Ignorados: {total_skipped}")
    print(f"Dry run: {DRY_RUN}")


if __name__ == "__main__":
    migrar_ids()
