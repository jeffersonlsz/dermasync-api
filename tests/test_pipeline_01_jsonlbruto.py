import pytest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from app.pipeline.a_extracao_bruta.gerar_jsonl_bruto import gerar_jsonl_bruto  # adapte para seu import real
import logging
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


# Teste para ler um diretorio temporário e gerar um arquivo JSONL bruto a partir de um arquivo .txt
# O teste deve garantir que o arquivo JSONL gerado tenha o formato correto e os campos obrigatórios estejam presentes.
# Além disso, deve validar o JSON contra um schema predefinido.
@pytest.mark.asyncio
async def test_gerar_jsonl_bruto_formato_valido():
    # 1. Cria diretório e arquivo .txt mockado
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "relato1.txt"
        txt_path.write_text("Relato de teste sobre coceira e pele seca.")

        output_path = Path(tmpdir) / "saida.jsonl"

        # 2. Chama a função alvo
        await gerar_jsonl_bruto({
            'origem': 'facebook',
            'src_dir': tmpdir,
            'ctx_id': '1234567890',
            'grupo': 'Dermatite Atópica Brasil',
            'tipo': 'comentario'
        }, output_path=output_path)

        # 3. Lê o resultado
        assert output_path.exists(), "Arquivo JSONL não foi gerado."
        linhas = output_path.read_text().splitlines()
        assert len(linhas) == 1, "Deveria conter uma linha por relato."

        # 4. Valida o JSON e campos obrigatórios
        dado = json.loads(linhas[0])
        logging.info("Dado gerado: %s", dado)
        assert isinstance(dado, dict), "O dado deve ser um objeto JSON."
        assert "id_relato" in dado
        assert "origem" in dado
        assert "versao_pipeline" in dado
        assert "plataforma" in dado["origem"]
        assert "data_modificacao" in dado
        assert "conteudo_original" in dado or "conteudo" in dado

        # 5. Valida tipos
        assert isinstance(dado["id_relato"], str)
        assert isinstance(dado["origem"], dict)
        assert isinstance(dado["data_modificacao"], str)
        datetime.fromisoformat(dado["data_modificacao"])  # lança erro se inválido

@pytest.mark.asyncio
async def test_valida_schema_jsonl_bruto():
    schema_path = Path("./app/schema/relato_schema.json")
    with open(schema_path, "r") as f:
        schema = json.load(f)

    with open("./app/pipeline/dados/jsonl_brutos/relatos-20250620-facebook-v0.0.1.jsonl", "r", encoding="utf-8") as f:
        for linha in f:
            dado = json.loads(linha)
            validate(instance=dado, schema=schema)  # lança erro se inválido