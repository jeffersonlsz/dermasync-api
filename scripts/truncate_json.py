# -*- coding: utf-8 -*-
import json
import argparse

def truncate_long_strings(data, max_len=50):
    """
    Percorre recursivamente uma estrutura de dados (dicionário ou lista)
    e trunca strings que excedam o comprimento máximo.

    Args:
        data: O dicionário ou lista a ser processado.
        max_len: O comprimento máximo da string antes de ser truncada.

    Returns:
        A estrutura de dados com as strings longas truncadas.
    """
    if isinstance(data, dict):
        # Retorna um novo dicionário com valores processados recursivamente
        return {key: truncate_long_strings(value, max_len) for key, value in data.items()}
    elif isinstance(data, list):
        # Retorna uma nova lista com itens processados recursivamente
        return [truncate_long_strings(item, max_len) for item in data]
    elif isinstance(data, str) and len(data) > max_len:
        # Trunca a string e adiciona '...'
        return data[:max_len] + '...'
    else:
        # Retorna números, booleanos, None e strings curtas como estão
        return data

def main():
    """
    Função principal para analisar argumentos de linha de comando e processar o arquivo.
    """
    parser = argparse.ArgumentParser(
        description="Lê um arquivo JSON ou JSONL, trunca strings longas (>50 caracteres) e imprime o resultado."
    )
    parser.add_argument("filepath", help="O caminho para o arquivo .json ou .jsonl a ser processado.")
    args = parser.parse_args()

    try:
        with open(args.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    json_obj = json.loads(line)
                    truncated_obj = truncate_long_strings(json_obj)
                    print(json.dumps(truncated_obj, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(f"Aviso: Ignorando linha que não é um JSON válido: {line[:100]}...")
    except FileNotFoundError:
        print(f"Erro: O arquivo não foi encontrado em '{args.filepath}'")

if __name__ == "__main__":
    main()