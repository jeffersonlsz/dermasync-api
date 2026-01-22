# app/services/llm/normalization.py

def strip_code_fences(text: str) -> str:
    """
    Remove code fences ``` / ```json e prefixos residuais como 'json'.
    Normalização de transporte apenas (sem semântica).
    """

    text = text.strip()

    if text.startswith("```"):
        text = text.split("```", 1)[1]

    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    text = text.strip()

    if text.lower().startswith("json"):
        lines = text.splitlines()
        if lines and lines[0].strip().lower() == "json":
            text = "\n".join(lines[1:]).strip()

    return text
