"""
Atualiza automaticamente seções do README.md
a partir de artefatos gerados pelo código (Mermaid, tabelas, etc).

Nunca sobrescreve o README inteiro.
Opera apenas dentro de blocos AUTO:*.
"""

from pathlib import Path
import re
import subprocess

# -------------------------------------------------
# Paths
# -------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"

STATE_MACHINE_PATH = ROOT / "docs" / "auto" / "relato_state_machine.mmd"
INTENTS_TABLE_PATH = ROOT / "docs" / "auto" / "relato_intents_table.md"


# -------------------------------------------------
# Utilidades básicas
# -------------------------------------------------

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
    *,
    wrap_in_mermaid: bool = False,
) -> str:
    """
    Substitui o conteúdo entre:

    <!-- AUTO:NAME:START -->
    <!-- AUTO:NAME:END -->

    Se wrap_in_mermaid=True, envolve o conteúdo em ```mermaid```
    """

    pattern = re.compile(
        rf"(<!-- AUTO:{block_name}:START -->)(.*?)(<!-- AUTO:{block_name}:END -->)",
        re.DOTALL,
    )

    if not pattern.search(readme):
        raise RuntimeError(f"Bloco AUTO:{block_name} não encontrado no README")

    if wrap_in_mermaid:
        replacement_body = f"\n```mermaid\n{new_content.strip()}\n```\n"
    else:
        replacement_body = f"\n{new_content.strip()}\n"

    replacement = r"\1" + replacement_body + r"\3"

    return pattern.sub(replacement, readme)


# -------------------------------------------------
# Etapas de geração
# -------------------------------------------------

def generate_state_machine():
    print("🧠 Gerando state machine Mermaid...")
    subprocess.run(
        ["python", "scripts/docs/generate_state_machine_mermaid.py"],
        cwd=ROOT,
        check=True,
    )


def generate_intents_table():
    print("📊 Gerando tabela de intents...")
    subprocess.run(
        ["python", "scripts/docs/generate_intents_table.py"],
        cwd=ROOT,
        check=True,
    )


# -------------------------------------------------
# Atualização do README
# -------------------------------------------------

def update_readme():
    print("📝 Atualizando README.md...")

    readme = read_file(README_PATH)

    # --- State machine ---
    state_machine = read_file(STATE_MACHINE_PATH)
    readme = replace_auto_block(
        readme,
        block_name="DOMAIN_STATE_MACHINE",
        new_content=state_machine,
        wrap_in_mermaid=True,
    )

    # --- Tabela de intents ---
    intents_table = read_file(INTENTS_TABLE_PATH)
    readme = replace_auto_block(
        readme,
        block_name="RELATO_INTENTS",
        new_content=intents_table,
        wrap_in_mermaid=False,
    )

    write_file(README_PATH, readme)
    print("✅ README.md atualizado com sucesso.")


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    generate_state_machine()
    generate_intents_table()
    update_readme()


if __name__ == "__main__":
    main()
