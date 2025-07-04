from pathlib import Path


def gerar_mermaid(fluxo, nome_arquivo="fluxo.mmd"):
    linhas = ["sequenceDiagram"]
    participantes = set()

    for log in fluxo:
        participantes.add(log.caller)
        participantes.add(log.callee)

    for p in participantes:
        linhas.append(f"    participant {p}")

    for log in fluxo:
        linhas.append(f"    {log.caller}->>{log.callee}: {log.operation}")

    # Garante que a pasta existe
    Path(nome_arquivo).parent.mkdir(parents=True, exist_ok=True)

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
