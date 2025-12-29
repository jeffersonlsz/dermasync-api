"""
Atualiza automaticamente seções do README.md
a partir de artefatos gerados pelo código (Mermaid, tree, rotas, etc).

Nunca sobrescreve o README inteiro.
Opera apenas dentro de blocos AUTO:*.
"""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"

STATE_MACHINE_PATH = ROOT / "docs" / "auto" / "relato_state_machine.mmd"


# -------------------------
# Utilidades
# -------------------------

def read_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def replace_auto_block(
    readme: str,
    block_name: str,
    new_content: str,
) -> str:
    """
    Substitui o conteúdo entre:
    <!-- AUTO:NAME:START -->
    <!-- AUTO:NAME:END -->
    """

    pattern = re.compile(
        rf"(<!-- AUTO:{block_name}:START -->)(.*?)(<!-- AUTO:{block_name}:END -->)",
        re.DOTALL,
    )

    replacement = (
        r"\1\n```mermaid\n"
        + new_content.strip()
        + "\n```\n"
        + r"\3"
    )

    if not pattern.search(readme):
        raise RuntimeError(f"Bloco AUTO:{block_name} não encontrado no README")

    return pattern.sub(replacement, readme)


# -------------------------
# Etapas
# -------------------------

def generate_state_machine():
    print("Gerando state machine Mermaid...")
    subprocess.run(
        ["python", "scripts/docs/generate_state_machine_mermaid.py"],
        cwd=ROOT,
        check=True,
    )


def update_readme():
    print("Atualizando README.md...")

    readme = read_file(README_PATH)
    state_machine = read_file(STATE_MACHINE_PATH)

    readme = replace_auto_block(
        readme,
        block_name="DOMAIN_STATE_MACHINE",
        new_content=state_machine,
    )

    write_file(README_PATH, readme)
    print("README.md atualizado com sucesso.")


# -------------------------
# Main
# -------------------------

def main():
    generate_state_machine()
    update_readme()


if __name__ == "__main__":
    main()
