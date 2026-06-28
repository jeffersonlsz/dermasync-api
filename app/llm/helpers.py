import re

def remove_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def fix_missing_commas(text: str) -> str:
    # adiciona vrgula entre strings consecutivas
    return re.sub(r'"\s*\n\s*"', '", "', text)