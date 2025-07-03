import json
from pathlib import Path

from jsonschema import ValidationError, validate


def validar_jsonl(caminho_jsonl, caminho_schema):
    with open(caminho_schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    erros = []
    with open(caminho_jsonl, "r", encoding="utf-8") as f:
        for i, linha in enumerate(f, start=1):
            try:
                dado = json.loads(linha)
                validate(instance=dado, schema=schema)
            except json.JSONDecodeError as e:
                erros.append(f"[Linha {i}] Erro de parsing JSON: {str(e)}")
            except ValidationError as e:
                erros.append(f"[Linha {i}] Violação do schema: {str(e.message)}")

    if not erros:
        print(f"✅ {caminho_jsonl} validado com sucesso.")
    else:
        print(f"❌ {len(erros)} erros encontrados:")
        for e in erros:
            print(" -", e)


if __name__ == "__main__":
    # Altere conforme necessário
    caminho_jsonl = "output/saida.jsonl"
    caminho_schema = "schema/relato_schema.json"
    validar_jsonl(caminho_jsonl, caminho_schema)
