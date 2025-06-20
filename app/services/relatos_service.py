from app.firestore.client import db
from app.logger_config import configurar_logger_json
import logging

# Para produção (chame uma vez no início do seu main ou serviço)
configurar_logger_json()

logger = logging.getLogger(__name__)

async def listar_relatos():
    logger.info("Iniciando a listagem de relatos")
    try:
        docs = db.collection("jornadas").stream()
        resultados = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  # Adiciona o ID do documento
            resultados.append(data)

        return resultados

    except Exception as e:
        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")
