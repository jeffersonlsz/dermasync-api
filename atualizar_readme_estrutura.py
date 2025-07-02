import os
import datetime
from pathlib import Path

# Caminho do projeto
ROOT = Path(__file__).parent
README = ROOT / "README.md"
BACKUP_DIR = ROOT / "docs"  # Onde salvaremos backups
BACKUP_DIR.mkdir(exist_ok=True)

# 1. Criar backup
def criar_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"README_backup_{timestamp}.md"
    if README.exists():
        backup_path.write_text(README.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup salvo em: {backup_path}")
    else:
        print("README.md original não encontrado.")

# 2. Gera estrutura de árvore estilo `tree`
def gerar_estrutura(path=".", prefix=""):
    ignore_dirs = {".git", "__pycache__", "venv", "node_modules", ".idea", ".vscode", ".pytest_cache", "prompts_privados", "temp_storage", "static/imagens"}
    tree = ""
    entries = sorted(os.listdir(path))
    for index, name in enumerate(entries):
        if name in ignore_dirs or name.startswith("."):
            continue
        full_path = os.path.join(path, name)
        connector = "└── " if index == len(entries) - 1 else "├── "
        tree += f"{prefix}{connector}{name}\n"
        if os.path.isdir(full_path):
            extension = "    " if index == len(entries) - 1 else "│   "
            tree += gerar_estrutura(full_path, prefix + extension)
    return tree

# 3. Gera resumo técnico automático
def gerar_resumo_tecnico():
    return """
## 🔧 Resumo Técnico

- **API**: FastAPI com rotas em `app/api`, organizadas por domínio.
- **Serviços**: Camada lógica está em `app/services` (e subpastas).
- **Integração com LLMs**: Em `app/llm`, com chamadas e prompts dinâmicos via `load_prompt`.
- **Pipeline de dados**: Com etapas modulares em `app/pipeline/scripts`.
- **ChromaDB**: Integração vetorial em `app/chroma`.
- **Firestore e Imagens**: Em `app/firestore/` e `routes/imagens.py`.
- **Deploy**: Automação com `Dockerfile`, `.bat` scripts e futura integração contínua.
"""

# 4. Atualiza o README com a nova estrutura
def atualizar_readme():
    titulo = "# 🌱 Projeto DermaSync – Estrutura Atualizada\n"
    imagem_arquitetura = "![Arquitetura DermaSync](docs/arquitetura-dermasync.png)\n"
    arvore = gerar_estrutura(".")
    resumo = gerar_resumo_tecnico()

    novo_conteudo = f"""{titulo}

## 📁 Estrutura de Pastas

{arvore}

{resumo}

🕓 Última atualização automática: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

## 📜 Detalhes do Projet
# 🌱 Projeto DermaSync – Estrutura Atualizada
{imagem_arquitetura}

"""

    README.write_text(novo_conteudo, encoding="utf-8")
    print("README.md atualizado com sucesso.")

# Execução principal
if __name__ == "__main__":
    criar_backup()
    atualizar_readme()
