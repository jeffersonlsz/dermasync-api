from app.firestore.client import get_firestore_client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

def salvar_relato_firestore(doc: dict, collection: str = "relatos-completos") -> str:
    logger.info(f"Salvando documento na coleção '{collection}': {doc['id']}")
    db = get_firestore_client()
    
    doc_ref = db.collection(collection).document(doc["id"])
    doc_ref.set(doc)
    logger.info(f"Documento salvo com sucesso: {doc['id']}")
    return doc["id"]