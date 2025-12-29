"""
Gera automaticamente uma tabela Markdown de intents
a partir do domínio (intents + transitions).

Fonte da verdade:
- app/domain/relato/intents.py
- app/domain/relato/transitions.py
"""
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to Python path so app module can be found
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus
from app.domain.relato.transitions import resolve_transition


OUTPUT_PATH = Path("docs/auto/relato_intents_table.md")


def generate_intents_matrix():
    """
    Retorna um dict:
    intent -> { from_states: set, to_states: set }
    """
    matrix = defaultdict(lambda: {"from": set(), "to": set()})

    all_intents = list(RelatoIntent)
    all_states = [None] + list(RelatoStatus)

    for intent in all_intents:
        for state in all_states:
            # relato_id é obrigatório para algumas transições
            result = resolve_transition(
                intent=intent, current_state=state, relato_id="dummy_id_for_script"
            )
            if result.allowed:
                from_state_str = state.value if state else "Nenhum (criação)"
                matrix[intent.value]["from"].add(from_state_str)
                if result.next_state:
                    matrix[intent.value]["to"].add(result.next_state.value)

    return matrix


def generate_markdown_table(matrix) -> str:
    lines = []
    lines.append("| Intent | Estados de Origem | Estado(s) de Destino |")
    lines.append("|-------|------------------|---------------------|")

    for intent, data in sorted(matrix.items()):
        from_states = ", ".join(sorted(data["from"]))
        to_states = ", ".join(sorted(data["to"]))
        lines.append(f"| `{intent}` | {from_states} | {to_states} |")

    return "\n".join(lines)


def main():
    matrix = generate_intents_matrix()
    table = generate_markdown_table(matrix)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(table, encoding="utf-8")

    print(f"Tabela de intents gerada em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
