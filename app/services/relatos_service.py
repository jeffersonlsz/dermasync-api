# app/services/relatos_service.py

"""
Este módulo contém os serviços relacionados aos relatos, como listagem e manipulação de dados.
"""

from datetime import datetime, timezone
import logging
import uuid

from app.firestore.client import get_firestore_client
from app.logger_config import configurar_logger_json

from app.archlog_sync.logger import registrar_log
# Para produção (chame uma vez no início do seu main ou serviço)
configurar_logger_json()

logger = logging.getLogger(__name__)


async def listar_relatos():
    logger.info("Iniciando a listagem de relatos")
    db = get_firestore_client()
    if not db:
        logger.info("Erro ao obter o cliente Firestore")
        raise Exception("Erro ao obter o cliente Firestore")
    try:
        
        docs = db.collection("relatos").stream()
        resultados = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  # Adiciona o ID do documento
            resultados.append(data)

        
        logger.info(f"Listagem de relatos concluída , total de {len(resultados)} relatos encontrados")

        return resultados

    except Exception as e:
        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")
