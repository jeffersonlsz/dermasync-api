# run_test_model.py
"""
Teste isolado do modelo LLM local (Ollama) para o prompt
EXTRACT_COMPUTABLE_METADATA v1.

Modo atual:
- Transporte normalizado
- JSON sempre parseado
- Validação em DOIS ESTÁGIOS:
    1) STRICT (tentativa)
    2) RELAXED (aceita payload bruto se falhar)

⚠️ Este relaxamento é TEMPORÁRIO e EXPLÍCITO,
apenas para acelerar desenvolvimento arquitetural.
"""

import json
import sys
from pprint import pprint

from app.domain.enrichment.prompts.extract_computable_metadata_v2 import (
    build_prompt,
    PROMPT_VERSION,
)
from app.domain.enrichment.schemas.enriched_metadata_v2 import EnrichedMetadataV2
from app.pipeline.llm_client.ollama_client import OllamaClient


# ------------------------------------------------------------
# NORMALIZAÇÃO DE TRANSPORTE (PERMITIDA)
# ------------------------------------------------------------

def extract_json_from_llm_output(text: str) -> str:
    """
    Extrai uma string JSON de uma saída de LLM que pode conter
    texto adicional, code fences (```json) ou tags (<output>).
    """
    # 1. Tenta encontrar bloco de código JSON delimitado por ```json
    if "```json" in text:
        json_block = text.split("```json", 1)[1]
        json_block = json_block.split("```", 1)[0]
        return json_block.strip()

    # 2. Tenta encontrar um JSON dentro de tags <output>
    if "<output>" in text:
        json_block = text.split("<output>", 1)[1]
        json_block = json_block.split("</output>", 1)[0]
        return json_block.strip()

    # 3. Fallback: encontra o primeiro '{' e o último '}'
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return text[start:end].strip()
    except ValueError:
        # Se não encontrar '{' ou '}', retorna o texto original para debug
        return text

# ------------------------------------------------------------
# CONFIGURAÇÃO DE TESTE
# ------------------------------------------------------------

RELATO_TESTE = """
Tenho dermatite desde criança. A coceira é muito forte,
principalmente nas dobras do cotovelo e nas mãos.
Além disso, notei que quando fico exposto ao sol por muito tempo,
minha pele fica ainda mais irritada.

Uso as pomadas Advantan e Tarfic, que me ajudam bastante
sempre que tenho crise. Também uso óleo de girassol.
Percebo que o estresse piora minha pele.
Uso hidratante diariamente.
"""


# ------------------------------------------------------------
# EXECUÇÃO
# ------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("TESTE ISOLADO — MODELO LLM LOCAL (Ollama)")
    print(f"Prompt version: {PROMPT_VERSION}")
    print("=" * 80)

    # 1. Construir prompt
    prompt = build_prompt(RELATO_TESTE)

    print("\n--- PROMPT (resumo) ---")
    print(prompt[:800] + "\n... [truncado]\n")

    # 2. Inicializar cliente LLM
    llm = OllamaClient()

    print(f"Modelo: {llm.model_name}")
    print("\nExecutando LLM...\n")

    # 3. Chamar modelo
    raw_output = llm.generate(prompt)

    print("--- OUTPUT CRU DO MODELO ---")
    print(raw_output)
    print("-" * 80)

    # 4. Normalizar transporte
    clean_output = extract_json_from_llm_output(raw_output)

    print("--- OUTPUT NORMALIZADO (SEM FENCES) ---")
    print(clean_output)
    print("-" * 80)

    # 5. Parse JSON (obrigatório)
    try:
        parsed = json.loads(clean_output)
    except json.JSONDecodeError as exc:
        print("X ERRO CRÍTICO: JSON inválido mesmo após normalização")
        print(exc)
        sys.exit(1)

    print("✅ JSON parseado com sucesso\n")

    print("--- JSON PARSEADO ---")
    pprint(parsed)
    print("-" * 80)

    # 6. VALIDAÇÃO EM DOIS MODOS
    print("🔎 Tentando validação STRICT (schema v2)...")

    try:
        enrichment = EnrichedMetadataV2.model_validate(parsed)
        print("✅ SCHEMA v2 VALIDADO (STRICT)\n")

        print("--- ENRICHMENT NORMALIZADO (STRICT) ---")
        pprint(enrichment.model_dump())

    except Exception as exc:
        print("⚠️ FALHA NA VALIDAÇÃO STRICT")
        print(exc)
        print("\n➡️ Entrando em MODO RELAXED (DEV ONLY)\n")

        print("--- ENRICHMENT ACEITO (RELAXED / SEM VALIDAÇÃO) ---")
        pprint(parsed)

        print("\n⚠️ ATENÇÃO:")
        print("- Este payload NÃO é semanticamente garantido")
        print("- Use apenas para desenvolvimento e testes arquiteturais")
        print("- Revalidação STRICT será necessária futuramente")

    print("=" * 80)
    print("🎉 TESTE CONCLUÍDO")
    print("Modo de validação: STRICT se possível, RELAXED se necessário")


if __name__ == "__main__":
    main()
