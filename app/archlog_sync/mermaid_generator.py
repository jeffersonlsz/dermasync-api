#  File: app/archlog_sync/mermaid_generator.py
# -*- coding: utf-8 -*-
"""
Este módulo contém funções para gerar diagramas de sequência em Mermaid a partir de eventos de log.
"""


def to_sequence_diagram(events: list[dict]) -> str:
    """
    Generate a Mermaid sequence diagram from a list of structured log events.

    Each event dict must have at least the keys:
      - "caller":   the name of the caller service/component
      - "callee":   the name of the callee service/component
      - "operation": a short description of the operation (e.g. HTTP method + path)

    Returns a string containing a valid Mermaid sequenceDiagram. If `events` is empty,
    it will still emit the “sequenceDiagram” header alone.
    """
    # Always start with the header
    lines = ["sequenceDiagram"]

    # Append one arrow line per event, preserving order
    for e in events:
        caller   = e.get("caller", "unknown")
        callee   = e.get("callee", "unknown")
        operation = e.get("operation", "")
        lines.append(f"{caller}->>{callee}: {operation}")

    return "\n".join(lines)



# Exemplo de uso:
if __name__ == "__main__":
    from .parser import parse_logs

    groups = parse_logs("app/archlog_sync/exemplos/relato_log.jsonl")
    diagram = to_sequence_diagram(groups["req_001"])
    print(diagram)
