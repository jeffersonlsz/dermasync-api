"""
Gera automaticamente um diagrama Mermaid (stateDiagram-v2)
a partir do domínio de relatos (states + transitions).

Fonte de verdade:
- app/domain/relato_status.py
- app/domain/relato/transitions.py
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path so app module can be found
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from app.domain.relato_status import RelatoStatus
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.transitions import resolve_transition


OUTPUT_PATH = Path("docs/auto/relato_state_machine.mmd")


def normalize(name: str) -> str:
    """Normaliza nomes para Mermaid (sem aspas, espaços etc)."""
    return name.replace("-", "_").replace(" ", "_")


def generate_mermaid_state_machine(
    states: list[str],
    transitions: Dict[Any, Any],
) -> str:
    lines = []
    lines.append("stateDiagram-v2")
    
    # Initial state transition
    create_result = resolve_transition(intent=RelatoIntent.CREATE_RELATO, current_state=None, relato_id="dummy_id")
    if create_result.allowed and create_result.next_state:
        lines.append(f"    [*] --> {normalize(create_result.next_state.value)} : {RelatoIntent.CREATE_RELATO.value}")

    for from_state, intents in transitions.items():
        for intent, to_state in intents.items():
            lines.append(
                f"    {normalize(from_state.value)} --> {normalize(to_state.value)} : {intent.value}"
            )
            
    # Add states that might not be in transitions
    all_states_in_transitions = {s.value for s in transitions.keys()} | {s.value for v in transitions.values() for s in v.values()}
    for state_val in states:
        if state_val not in all_states_in_transitions:
             # Just declare the state
             lines.append(f"    state {normalize(state_val)}")


    return "\n".join(lines)


def build_transitions_dict() -> Dict[RelatoStatus, Dict[RelatoIntent, RelatoStatus]]:
    """
    Constrói um dicionário de transições válidas para a máquina de estados.
    """
    transitions: Dict[RelatoStatus, Dict[RelatoIntent, RelatoStatus]] = {}
    for from_state in RelatoStatus:
        transitions[from_state] = {}
        for intent in RelatoIntent:
            if intent == RelatoIntent.CREATE_RELATO:
                continue  # Handled as initial transition

            result = resolve_transition(intent=intent, current_state=from_state, relato_id="dummy_id")
            if result.allowed and result.next_state:
                transitions[from_state][intent] = result.next_state
    return transitions


def main():
    """
    Gera o diagrama e o escreve no arquivo de saída.
    """
    states = [state.value for state in RelatoStatus]
    
    transitions = build_transitions_dict()

    mermaid = generate_mermaid_state_machine(
        states=states,
        transitions=transitions,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(mermaid, encoding="utf-8")

    print(f"State machine Mermaid gerado em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()