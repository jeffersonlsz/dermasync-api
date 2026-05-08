# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido para enriquecimento.")

    return f"""
Extraia os dados do relato e retorne APENAS JSON válido.

REGRAS:
- sem markdown
- sem comentários
- sem texto extra
- não inventar dados
- lowercase
- sem duplicatas em listas
- usar null quando ausente
- manter exatamente as chaves abaixo

SCHEMA:
{{
  "idade": null,
  "genero": null,
  "sintomas": [],
  "tratamentos_mencionados": []
}}

REGRAS SEMÂNTICAS:
- idade: inteiro apenas se explícito
- genero:
  - homem -> masculino
  - mulher -> feminino
  - ambíguo -> null
- sintomas:
  - apenas sintomas físicos/dermatológicos
  - usar termos curtos
  - exemplo: "coceira intensa" -> "coceira"
- tratamentos_mencionados:
  - medicamentos, terapias ou práticas
  - exemplo: hidratante, corticoide, banho morno

RELATO:
{relato_text}
""".strip()