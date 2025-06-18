import json

DADOS_VIDEOS_ENRIQUECIDOS = 'app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-20250609-v.jsonl'
def ler_jsonl_videos():
    """
    Reads the contents of the JSONL file 'jsonl_enriquecidos/relatos_enriquecidos.jsonl'
    and returns its contents as a list of dictionaries.
    """
    file_path = DADOS_VIDEOS_ENRIQUECIDOS
    contents = []
    print(f"Lendo arquivo {DADOS_VIDEOS_ENRIQUECIDOS} ...")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                contents.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    
    return contents

