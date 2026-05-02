# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:
    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido para enriquecimento.")

    return f"""
Você é um sistema de extração semântica determinística.

Sua tarefa é converter o relato em um JSON ESTRITAMENTE válido,
seguindo exatamente o schema abaixo.

REGRAS ABSOLUTAS (quebra = resposta inválida):
- Retorne APENAS JSON válido (sem texto antes ou depois)
- NÃO use markdown
- NÃO inclua comentários
- NÃO invente campos
- NÃO omita campos obrigatórios
- NÃO altere os nomes das chaves
- NÃO use valores fora do domínio especificado

FORMATAÇÃO:
- Todas as strings devem estar em lowercase
- Remover espaços desnecessários
- Listas não podem conter duplicatas
- Listas devem conter apenas strings simples (sem frases longas)
- Se não houver dados: usar null (para escalares) ou [] (para listas)

SCHEMA OBRIGATÓRIO (seguir ORDEM EXATA):

{{
  "idade": int | null,
  "genero": "masculino" | "feminino" | "outro" | null,
  "sintomas": string[],
  "tratamentos_mencionados": string[]
}}

REGRAS SEMÂNTICAS:

- idade:
  - Extrair apenas se explicitamente mencionada
  - Converter para inteiro
  - Ignorar estimativas vagas ("na casa dos 30")

- genero:
  - Mapear:
    - "homem", "masculino" ? "masculino"
    - "mulher", "feminino" ? "feminino"
  - Caso ambíguo ? null

- sintomas:
  - Extrair apenas sintomas físicos ou dermatológicos
  - Normalizar termos (ex: "coceira intensa" ? "coceira")
  - Evitar frases completas

- tratamentos_mencionados:
  - Extrair nomes de medicamentos, terapias ou práticas
  - Ex: "hidratante", "corticoide", "banho morno"
  - Não incluir opiniões ou resultados

RELATO:
\"\"\"
{relato_text}
\"\"\"
""".strip()
