# app/archlog_sync/logger.py
# -*- coding: utf-8 -*-
"""Este módulo contém funções para registrar logs de eventos de forma estruturada em um arquivo JSONL."""
import json
import logging
from datetime import datetime
from pathlib import Path

from .schemas import LogEntry

# Configuração do logger

logger = logging.getLogger(__name__)

LOG_FILE = Path("logs/structured_logs.jsonl")


async def registrar_log(log_data: dict):
    logger.info("Registrando log: %s", log_data)
    """
    Recebe um log_data como dict com todas as chaves de LogEntry,
    valida com Pydantic e grava em JSONL.
    """
    # cria o modelo Pydantic diretamente a partir do dict
    entry = LogEntry(**log_data)
    logger.info("LogEntry validado: %s", entry)
    logger.info("Caminho do logfile: %s", LOG_FILE.absolute())
    # grava linha JSONL (já inclui a timestamp que veio no log_data)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")
        f.flush()
    logger.info("Log registrado com sucesso: %s", entry)
