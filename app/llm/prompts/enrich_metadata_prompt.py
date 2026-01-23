# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:
    """
    Constrói o prompt canônico para enriquecimento semântico de um relato.

    Responsabilidade:
    - Receber texto humano bruto
    - Retornar prompt determinístico
    - NÃO chamar LLM
    - NÃO parsear resposta
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido para enriquecimento.")

    return f"""
Você é um sistema de extração semântica.

Seu objetivo é analisar o relato abaixo e extrair informações
estruturadas em formato JSON.

⚠️ Regras obrigatórias:
- Retorne APENAS JSON válido
- Não use markdown
- Não inclua explicações
- Use null quando a informação não estiver presente

Campos esperados:
- idade: número inteiro ou null
- genero: "masculino", "feminino", "outro" ou null
- sintomas: lista de strings (pode ser vazia)
- tratamentos_mencionados: lista de strings (pode ser vazia)

Relato:
\"\"\"
{relato_text}
\"\"\"
""".strip()
