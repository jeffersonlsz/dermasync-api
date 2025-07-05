#  File: app/archlog_sync/mermaid_generator.py
# -*- coding: utf-8 -*-
"""
Este módulo contém funções para gerar diagramas de sequência em Mermaid a partir de eventos de log.
"""


def to_sequence_diagram(events: list[dict]) -> str:
    lines = ["sequenceDiagram"]
    for e in events:
        caller = e["caller"]
        callee = e["callee"]
        op = e["operation"]
        lines.append(f"    {caller}->>{callee}: {op}")
        lines = ["sequenceDiagram"]
        for e in events:
            caller = e["caller"]
            callee = e["callee"]
            op = e["operation"]
            # sem indentação para passar no teste
            lines.append(f"{caller}->>{callee}: {op}")
        return "\n".join(lines)


# Exemplo de uso:
if __name__ == "__main__":
    from .parser import parse_logs

    groups = parse_logs("app/archlog_sync/exemplos/relato_log.jsonl")
    diagram = to_sequence_diagram(groups["req_001"])
    print(diagram)
