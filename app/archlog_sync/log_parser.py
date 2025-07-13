import json
import logging
from collections import defaultdict

from .schemas import LogEntry

# Configuração do logger
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def carregar_logs(caminho_arquivo):
    logger.info(f"Carregando logs do arquivo: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = [LogEntry(**json.loads(linha)) for linha in f]
            return linhas
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        logger.exception("Erro ao carregar logs")
        return []
    finally:
        logger.info(f"Logs carregados com sucesso do arquivo: {caminho_arquivo}")


#
def agrupar_por_request_id(logs):
    logger.info("Agrupando logs por request_id")
    logger.debug(f"Total de logs para agrupar: {len(logs)}")
    if not logs:
        logger.warning("Nenhum log encontrado para agrupar.")
        return {}
    fluxos = defaultdict(list)
    for log in logs:
        fluxos[log.request_id].append(log)

    logger.info(f"Total de fluxos agrupados: {len(fluxos)}")
    return dict(fluxos)
