import json
import logging
import sys

#
# Para logs diferentes por ambiente (dev, prod, test): use uma variável de ambiente e
# condicional
#


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record, ensure_ascii=False)


def configurar_logger_json(
    nivel=logging.INFO, para_arquivo=False, nome_arquivo="app.log"
):
    logger = logging.getLogger()
    logger.setLevel(nivel)
    logger.handlers = []  # limpa handlers antigos

    formatter = JsonFormatter()

    if para_arquivo:
        handler = logging.FileHandler(nome_arquivo)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)
