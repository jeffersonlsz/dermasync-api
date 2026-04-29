# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:
    """
    ConstrÃ³i o prompt canÃ´nico para enriquecimento semÃ¢ntico de um relato.

    Responsabilidade:
    - Receber texto humano bruto
    - Retornar prompt determinÃ­stico
    - NÃƒO chamar LLM
    - NÃƒO parsear resposta
    """

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou invÃ¡lido para enriquecimento.")

    return f"""
VocÃª Ã© um sistema de extraÃ§Ã£o semÃ¢ntica.

Seu objetivo Ã© analisar o relato abaixo e extrair informaÃ§Ãµes
estruturadas em formato JSON.

âš ï¸ Regras obrigatÃ³rias:
- Retorne APENAS JSON vÃ¡lido
- NÃ£o use markdown
- NÃ£o inclua explicaÃ§Ãµes
- Use null quando a informaÃ§Ã£o nÃ£o estiver presente

Campos esperados:
- idade: nÃºmero inteiro ou null
- genero: "masculino", "feminino", "outro" ou null
- sintomas: lista de strings (pode ser vazia)
- tratamentos_mencionados: lista de strings (pode ser vazia)

Relato:
\"\"\"
{relato_text}
\"\"\"
""".strip()
