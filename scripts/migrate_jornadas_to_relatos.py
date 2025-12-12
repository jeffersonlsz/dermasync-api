#!/usr/bin/env python3
"""
Migration script: Copies all documents from 'jornadas' collection to 'relatos' collection.
Preserves document IDs.

Usage:
  python scripts/migrate_jornadas_to_relatos.py          # Dry-run
  python scripts/migrate_jornadas_to_relatos.py --apply  # Execute migration
"""

import argparse
import logging
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.firestore.client import get_firestore_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("migrate_jornadas_relatos")

# NOTE: Using 'jornadas' (plural) as source based on existing scripts (read_from_firestore.py).
# If the actual collection is 'jornada', please update SOURCE_COLLECTION below.
SOURCE_COLLECTION = "jornadas"
DEST_COLLECTION = "relatos"

def run_migration(apply: bool, batch_size: int = 400):
    """
    Reads all docs from SOURCE_COLLECTION and writes them to DEST_COLLECTION.
    """
    db = get_firestore_client()
    source_ref = db.collection(SOURCE_COLLECTION)
    dest_ref = db.collection(DEST_COLLECTION)

    logger.info(f"Preparing to migrate from '{SOURCE_COLLECTION}' to '{DEST_COLLECTION}'.")
    if not apply:
        logger.info("DRY-RUN MODE: No changes will be written. Use --apply to execute.")

    # Stream documents (memory efficient for large collections)
    docs = source_ref.stream()
    
    batch = db.batch()
    count = 0
    total_processed = 0
    
    for doc in docs:
        data = doc.to_dict()
        # Use the same ID for the new document
        new_doc_ref = dest_ref.document(doc.id)
        
        if apply:
            batch.set(new_doc_ref, data)
        else:
            logger.info(f"[Dry-Run] Would copy doc {doc.id} to {DEST_COLLECTION}")

        count += 1
        total_processed += 1

        # Firestore batch limit is 500. We use 400 to be safe.
        if count >= batch_size:
            if apply:
                batch.commit()
                logger.info(f"Committed batch of {count} documents.")
            batch = db.batch()
            count = 0

    # Commit any remaining documents
    if count > 0:
        if apply:
            batch.commit()
            logger.info(f"Committed final batch of {count} documents.")
        else:
            logger.info(f"[Dry-Run] Would commit final batch of {count} documents.")

    logger.info(f"Migration finished. Total documents processed: {total_processed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate documents from 'jornadas' to 'relatos'.")
    parser.add_argument("--apply", action="store_true", help="Apply changes to Firestore.")
    args = parser.parse_args()

    try:
        run_migration(args.apply)
    except Exception as e:
        logger.exception("Migration failed: %s", e)
        sys.exit(1)