import json
import logging
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

from .utils import gerar_imagem_fake_base64

logger = logging.getLogger(__name__)

client = TestClient(app)


def criar_payload_valido():
    imagem_antes = gerar_imagem_fake_base64()
    imagem_durante = gerar_imagem_fake_base64()
    imagem_depois = gerar_imagem_fake_base64()

    return {
        "id": uuid.uuid4().hex[:8],
        "id_relato": uuid.uuid4().hex[:8],
        "conteudo_original": "Paciente com eczema severo nas costas.",
        "classificacao_etaria": "adulto",
        "idade": "35",
        "genero": "feminino",
        "sintomas": ["coceira", "descamação"],
        "regioes_afetadas": ["costas"],
        "imagens": {
            "antes": imagem_antes,
            "durante": [imagem_durante],
            "depois": imagem_depois,
        },
    }


def test_logger_config():
    logger.info("TESTE: Esta mensagem deve aparecer!")
    assert True


def test_enviar_relato_completo_valido():
    payload = criar_payload_valido()
    response = client.post("/relatos/enviar-relato-completo", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert isinstance(data["id"], str)
    assert len(data["imagens"]) >= 1  # Pelo menos 'antes'
    assert data["document_id"]  # Verifica se o ID do documento foi retornado


def test_relato_invalido_sem_conteudo():
    payload = criar_payload_valido()
    payload["conteudo_original"] = ""

    response = client.post("/relatos/enviar-relato-completo", json=payload)
    assert response.status_code == 400
    assert "Relato não pode estar vazio" in response.text


def test_relato_apenas_com_imagem_antes():
    imagem_antes = gerar_imagem_fake_base64()

    payload = {
        "id_relato": "relato_solo",
        "conteudo_original": "Dermatite na perna esquerda.",
        "idade": "20-25",
        "genero": "masculino",
        "sintomas": ["vermelhidão"],
        "regioes_afetadas": ["perna"],
        "imagens": {"antes": imagem_antes},
    }

    response = client.post("/relatos/enviar-relato-completo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["imagens"]


def test_relato_multiplas_durante_e_sem_depois():
    imagens_durante = [gerar_imagem_fake_base64() for _ in range(3)]
    imagem_antes = gerar_imagem_fake_base64()

    payload = {
        "id_relato": "relato_durante",
        "conteudo_original": "Melhora gradual com uso de óleo.",
        "idade": "30-35",
        "genero": "feminino",
        "sintomas": ["ressecamento", "coceira"],
        "regioes_afetadas": ["braços"],
        "imagens": {"antes": imagem_antes, "durante": imagens_durante, "depois": None},
    }

    response = client.post("/relatos/enviar-relato-completo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["imagens"]  # 1 antes + 3 durante
