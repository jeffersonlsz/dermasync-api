import pytest
from app.logger_config import configurar_logger_json

@pytest.fixture(autouse=True)
def configurar_logger_para_testes():
    configurar_logger_json(nivel="INFO", para_arquivo=False)
