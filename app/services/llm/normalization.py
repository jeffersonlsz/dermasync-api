# app/services/llm/normalization.py
import re

def strip_code_fences(text: str) -> str:
    """
    Remove ANSI escape sequences, extra text before/after JSON (like 'Thinking...'),
    code fences ``` / ```json e prefixos residuais como 'json'.
    Normalizao de transporte apenas (sem semntica).
    """
    # 1. Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)

    # 2. Extract JSON block based on outer {} or []
    start_dict = text.find('{')
    start_list = text.find('[')
    
    start_idx = -1
    if start_dict != -1 and start_list != -1:
        start_idx = min(start_dict, start_list)
    elif start_dict != -1:
        start_idx = start_dict
    elif start_list != -1:
        start_idx = start_list

    if start_idx != -1:
        is_dict = text[start_idx] == '{'
        end_char = '}' if is_dict else ']'
        end_idx = text.rfind(end_char)
        if end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx+1]

    text = text.strip()

    # 3. Fallbacks para markdown fences
    if text.startswith("```"):
        try:
            text = text.split("```", 1)[1]
        except IndexError:
            pass

    if text.endswith("```"):
        try:
            text = text.rsplit("```", 1)[0]
        except IndexError:
            pass

    text = text.strip()

    if text.lower().startswith("json"):
        lines = text.splitlines()
        if lines and lines[0].strip().lower() == "json":
            text = "\n".join(lines[1:]).strip()

    return text
