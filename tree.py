import fnmatch
import os
from pathlib import Path


def print_directory_tree(start_path=".", ignore_patterns=None, indent="", prefix=""):
    """
    Retorna a árvore de diretórios a partir do caminho especificado, ignorando padrões fornecidos.
    """
    if ignore_patterns is None:
        ignore_patterns = []

    start_path = Path(start_path).resolve()
    items = []

    for item in start_path.iterdir():
        should_ignore = False
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(item.name, pattern) or (
                item.is_dir() and pattern in item.name
            ):
                should_ignore = True
                break
        if not should_ignore:
            items.append(item)

    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = []

    for index, item in enumerate(items):
        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "
        line = f"{indent}{prefix}{connector}{item.name}"
        lines.append(line)

        if item.is_dir():
            new_prefix = "    " if is_last else "│   "
            sub_tree = print_directory_tree(
                start_path=item,
                ignore_patterns=ignore_patterns,
                indent=indent + new_prefix,
                prefix="",
            )
            lines.extend(sub_tree.splitlines())

    return "\n".join(lines)


def main():
    # Exemplos de padrões a ignorar
    ignore_patterns = [
        "*.pyc",  # Ignora arquivos .pyc
        "__pycache__",  # Ignora diretório __pycache__
        "venv",  # Ignora diretório venv
        ".git",  # Ignora diretório .git
        "node_modules",  # Ignora diretório node_modules
        "*.log",  # Ignora arquivos de log
        ".pytest_cache",  # Ignora diretório de cache do pytest
        ".vscode",  # Ignora diretório de configuração do VSCode
        "htmlcov",  # Ignora diretório de cobertura HTML
    ]

    try:
        print(f"Árvore de diretórios para: {Path('.').resolve()}")
        print_directory_tree(ignore_patterns=ignore_patterns)
    except Exception as e:
        print(f"Erro ao gerar a árvore de diretórios: {e}")


if __name__ == "__main__":
    main()
