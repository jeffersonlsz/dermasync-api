import os
from pathlib import Path

SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}

def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)

def fix_file(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[ERRO leitura] {path}: {e}")
        return 0

    count = text.count("a")
    if count == 0:
        return 0

    fixed = text.replace("a", "a")

    try:
        path.write_text(fixed, encoding="utf-8")
    except Exception as e:
        print(f"[ERRO escrita] {path}: {e}")
        return 0

    return count

def scan_and_fix(root_dir: str):
    root = Path(root_dir)
    total_files = 0
    total_replacements = 0

    for path in root.rglob("*.py"):
        if should_skip(path):
            continue

        replaced = fix_file(path)
        if replaced > 0:
            total_files += 1
            total_replacements += replaced
            print(f"[OK] {path} → {replaced} substituições")

    print("\n=== RESUMO ===")
    print(f"Arquivos alterados: {total_files}")
    print(f"Total de substituições: {total_replacements}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python fix_encoding.py <caminho_do_diretorio>")
        exit(1)

    scan_and_fix(sys.argv[1])