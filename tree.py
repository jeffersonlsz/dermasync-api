import os
from pathlib import Path
import fnmatch

def print_directory_tree(start_path='.', ignore_patterns=None, indent='', prefix=''):
    """
    Imprime a árvore de diretórios a partir do caminho especificado, ignorando padrões fornecidos.
    
    Args:
        start_path (str): Caminho inicial (padrão: diretório atual)
        ignore_patterns (list): Lista de padrões para ignorar (ex: ['*.pyc', 'venv'])
        indent (str): String de indentação para controle visual
        prefix (str): Prefixo para cada linha da árvore
    """
    if ignore_patterns is None:
        ignore_patterns = []
    
    # Converte o caminho para Path object
    start_path = Path(start_path).resolve()
    
    # Lista para armazenar itens do diretório
    items = []
    
    # Coleta todos os itens do diretório
    for item in start_path.iterdir():
        # Verifica se o item deve ser ignorado
        should_ignore = False
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(item.name, pattern) or (item.is_dir() and pattern in item.name):
                should_ignore = True
                break
        if not should_ignore:
            items.append(item)
    
    # Ordena itens (diretórios primeiro, depois arquivos)
    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    
    # Itera sobre os itens
    for index, item in enumerate(items):
        is_last = index == len(items) - 1
        # Define os conectores da árvore
        connector = '└── ' if is_last else '├── '
        
        # Imprime o item atual
        print(f"{indent}{prefix}{connector}{item.name}")
        
        # Se for um diretório, faz a recursão
        if item.is_dir():
            # Define o prefixo para os subitens
            new_prefix = '    ' if is_last else '│   '
            print_directory_tree(
                start_path=item,
                ignore_patterns=ignore_patterns,
                indent=indent + new_prefix,
                prefix=''
            )

def main():
    # Exemplos de padrões a ignorar
    ignore_patterns = [
        '*.pyc',        # Ignora arquivos .pyc
        '__pycache__',  # Ignora diretório __pycache__
        'venv',         # Ignora diretório venv
        '.git',         # Ignora diretório .git
        'node_modules', # Ignora diretório node_modules
        '*.log'         # Ignora arquivos de log
    ]
    
    try:
        print(f"Árvore de diretórios para: {Path('.').resolve()}")
        print_directory_tree(ignore_patterns=ignore_patterns)
    except Exception as e:
        print(f"Erro ao gerar a árvore de diretórios: {e}")

if __name__ == "__main__":
    main()