import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


@pytest.mark.asyncio
async def test_integracao_fase_01_e_02():
    from jsonschema import validate

    from app.pipeline.a_extracao_bruta.gerar_jsonl_bruto import gerar_jsonl_bruto
    from app.pipeline.B_enriquecimento.enriquecer_metadados import processar_relato

    schema_path = Path("./app/schema/relato_schema.json")
    assert schema_path.exists(), "Schema JSON não encontrado."
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # === Etapa 1: Gerar JSONL bruto ===
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "teste_relato.txt"
        txt_path.write_text(
            "Tenho 35 anos e usei Cetaphil por 10 dias. Ajudou bastante nas coceiras."
        )

        output_jsonl = Path(tmpdir) / "saida.jsonl"
        await gerar_jsonl_bruto(
            {
                "origem": "facebook",
                "src_dir": tmpdir,
                "ctx_id": "CTX1234567890",
                "grupo": "Grupo de Teste",
                "tipo": "comentario",
            },
            output_path=output_jsonl,
        )

        assert output_jsonl.exists(), "Arquivo JSONL bruto não foi gerado."

        linhas = output_jsonl.read_text().splitlines()
        assert len(linhas) == 1, "Deveria conter um único relato gerado."

        relato_bruto = json.loads(linhas[0])
        assert isinstance(relato_bruto, dict)

        # === Etapa 2: Enriquecer relato ===
        enriquecido = processar_relato(relato_bruto)
        assert isinstance(enriquecido, dict)

        # === Checa campos esperados após enriquecimento ===
        for campo in [
            "idade",
            "genero",
            "classificacao_etaria",
            "llm_processamento",
            "status_llm",
        ]:
            assert campo in enriquecido, f"Campo {campo} ausente após enriquecimento."

        # === Validação contra o schema ===
        try:
            validate(instance=enriquecido, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Erro na validação do schema enriquecido: {e.message}")
