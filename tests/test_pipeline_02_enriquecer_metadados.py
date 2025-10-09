import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import logging
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from jsonschema import ValidationError, validate

from app.pipeline.B_enriquecimento.enriquecer_metadados import processar_relato

logger = logging.getLogger(__name__)


@pytest.fixture
def relato_real():
    return {
        "id_relato": "5ab7a3b6132f409aacd90a3097ad4ceb",
        "origem": {
            "plataforma": "facebook",
            "link": None,
            "tipo": "comentario",
            "ano_postagem": None,
            "grupo": "Dermatite Atópica Brasil",
            "ctx_id": "1234567890",
        },
        "versao_pipeline": "v0.0.1",
        "data_modificacao": "2025-06-10T07:58:35.656562",
        "conteudo_original": "Queridos, tudo bom? ...",
    }


def test_enriquecer_metadados_formato_valido(mocker, relato_real):
    mock_llm_response_idade_genero = {
        "idade": 30,
        "genero": "feminino",
        "classificacao_etaria": "adulto",
    }
    mock_llm_response_tags = {
        "sintomas": ["coceira"],
        "produtos_naturais": [],
        "terapias_realizadas": [],
        "medicamentos": [],
    }

    mock_completar = MagicMock(
        side_effect=[
            json.dumps(mock_llm_response_idade_genero),
            json.dumps(mock_llm_response_tags),
        ]
    )

    mocker.patch(
        "app.pipeline.B_enriquecimento.enriquecer_metadados.get_llm_client",
        return_value=MagicMock(completar=mock_completar),
    )

    enriquecido = processar_relato(relato_real)
    logger.debug("Relato enriquecido: %s", enriquecido)

    assert "idade" in enriquecido
    assert "genero" in enriquecido
    assert "classificacao_etaria" in enriquecido
    assert "llm_processamento" in enriquecido
    assert "status_llm" in enriquecido
    assert enriquecido["status_llm"] in ["concluido", "erro"]

    schema_path = Path("./app/schema/relato_schema.json")
    assert schema_path.exists(), "Arquivo de schema JSON não encontrado."

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=enriquecido, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Erro de schema: {e.message}")


def test_if_jsonl_linha_valido():
    schema_path = Path("./app/schema/relato_schema.json")
    with open(schema_path, "r") as f:
        schema = json.load(f)

    linha = {
        "id_relato": "5ab7a3b6132f409aacd90a3097ad4ceb",
        "origem": {
            "plataforma": "facebook",
            "link": None,
            "tipo": "comentario",
            "ano_postagem": None,
            "grupo": "Dermatite Atópica Brasil",
        },
        "versao_pipeline": "v0.0.1",
        "data_modificacao": "2025-06-10T07:58:35.656562",
        "conteudo_original": "...",
        "idade": 22,
        "genero": "feminino",
        "classificacao_etaria": "adulto",
        "quadro_clinico": {
            "sintomas_descritos": [
                "pele ressecada",
                "atopias (alergias)",
                "pruridos (coceiras)",
                "ceratose pilar",
                "aspecto craquelê",
            ]
        },
        "intervencoes_produtos_naturais": ["Óleo de semente de uva"],
        "intervencoes_terapias_realizadas": [],
        "intervencoes_medicamentos": [
            {
                "nome_comercial": "Cetaphil Loção hidratante",
                "frequencia_uso": "ausente",
                "tempo_uso": "ausente",
            },
            {
                "nome_comercial": "Lipikar Loção",
                "frequencia_uso": "ausente",
                "tempo_uso": "ausente",
            },
            {
                "nome_comercial": "Bepantol solução",
                "frequencia_uso": "ausente",
                "tempo_uso": "ausente",
            },
            {
                "nome_comercial": "Cicaplast",
                "frequencia_uso": "1x ao dia, pela noite, ou 2x ao dia",
                "tempo_uso": "4 meses",
            },
        ],
        "llm_processamento": {
            "inicio": "2025-06-20T14:21:07.610044",
            "fim": "2025-06-20T14:21:09.652177",
            "duracao_ms": 2042,
            "tentativas": 1,
            "erro": None,
        },
        "status_llm": "concluido",
    }

    assert isinstance(linha, dict), "A linha deve ser um objeto JSON."
    validate(instance=linha, schema=schema)
