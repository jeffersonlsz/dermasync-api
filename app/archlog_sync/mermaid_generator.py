#  File: app/archlog_sync/mermaid_generator.py
# -*- coding: utf-8 -*-

import sys

"""
Este módulo contém funções para gerar diagramas de sequência em Mermaid a partir de eventos de log.
"""

from .parser import parse_logs


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
        caller = e.get("caller", "unknown")
        callee = e.get("callee", "unknown")
        operation = e.get("operation", "")
        lines.append(f"{caller}->>{callee}: {operation}")

    return "\n".join(lines)


# Exemplo de uso:
if __name__ == "__main__":

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        groups = parse_logs(file_path)
        for req_id, entries in groups.items():
            diagram = to_sequence_diagram(entries)
            print(f"Diagram for {req_id}:\n{diagram}\n")
    else:
        print("Usage: python mermaid_generator.py <path_to_log_file>")
