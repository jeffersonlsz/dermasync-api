import os

IGNORAR = {'.git', '__pycache__', 'venv', '.idea', '.mypy_cache'}

def listar_estrutura(caminho='.', prefixo=''):
    linhas = []
    for item in sorted(os.listdir(caminho)):
        if item in IGNORAR or item.startswith('.'):
            continue
        path = os.path.join(caminho, item)
        linhas.append(f"{prefixo}├── {item}")
        if os.path.isdir(path):
            # Verifica se o subdiretório está na lista ignorada
            if os.path.basename(path) not in IGNORAR:
                linhas += listar_estrutura(path, prefixo + '│   ')
    return linhas

def atualizar_readme():
    estrutura = listar_estrutura('.')
    bloco_inicio = "<!-- ESTRUTURA_INICIO -->"
    bloco_fim = "<!-- ESTRUTURA_FIM -->"

    with open("README.md", "r", encoding="utf-8") as f:
        conteudo = f.read()

    nova_estrutura = f"{bloco_inicio}\n```\n" + "\n".join(estrutura) + "\n```\n" + bloco_fim

    if bloco_inicio in conteudo and bloco_fim in conteudo:
        conteudo = conteudo.split(bloco_inicio)[0] + nova_estrutura + conteudo.split(bloco_fim)[1]
    else:
        conteudo += f"\n\n{nova_estrutura}"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(conteudo)

if __name__ == "__main__":
    atualizar_readme()
