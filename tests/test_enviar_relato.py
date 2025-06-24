import pytest
from fastapi.testclient import TestClient
from app.main import app
from .utils import gerar_imagem_fake_base64

client = TestClient(app)

def test_enviar_relato_completo_valido():
    imagem_base64 = gerar_imagem_fake_base64()

    payload = {
        "nome_arquivo": "teste_integra",
        "relato_texto": "Paciente relatou coceira intensa nas pernas.",
        "idade_aproximada": "30-35",
        "genero": "feminino",
        "sintomas": ["coceira", "vermelhidão"],
        "regioes_afetadas": ["pernas", "braços"],
        "imagens": [imagem_base64]
    }

    response = client.post("relatos/enviar-relato-completo", json=payload)
    
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "sucesso"
    assert "id" in data
    assert isinstance(data["id"], str)
    assert len(data["imagens"]) == 1
    assert data["imagens"][0].endswith(".jpg")
