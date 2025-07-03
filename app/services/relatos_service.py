# app/services/relatos_service.py

"""
Este módulo contém os serviços relacionados aos relatos, como listagem e manipulação de dados.
"""

import logging

from app.firestore.client import get_firestore_client
from app.logger_config import configurar_logger_json

# Para produção (chame uma vez no início do seu main ou serviço)
configurar_logger_json()

logger = logging.getLogger(__name__)


async def listar_relatos():
    logger.info("Iniciando a listagem de relatos")
    db = get_firestore_client()
    try:
        docs = db.collection("relatos").stream()
        resultados = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  # Adiciona o ID do documento
            resultados.append(data)

        return resultados

    except Exception as e:
        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")
