import datetime
import os
from pathlib import Path

from tree import print_directory_tree as gerar_estrutura

# Caminho do projeto
ROOT = Path(__file__).parent
print(f"ðŸŒ± Iniciando atualizaÃ§Ã£o do README na pasta: {ROOT}")
README = ROOT / "README.md"
BACKUP_DIR = ROOT / "docs"  # Onde salvaremos backups
BACKUP_DIR.mkdir(exist_ok=True)


# 1.1 Criar backup
def criar_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"README_backup_{timestamp}.md"
    if README.exists():
        backup_path.write_text(README.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup salvo em: {backup_path}")
    else:
        print("README.md original nÃ£o encontrado.")


# 1.2 Carrega diagrama Mermaid
def carregar_arquivo_mermaid():
    path = Path("docs/diagram.mmd")
    if path.exists():
        return f"```mermaid\n{path.read_text(encoding='utf-8')}\n```"
    return "âš ï¸ Diagrama em texto (Mermaid) nÃ£o disponÃ­vel.\n"


# 2. Gera estrutura de Ã¡rvore estilo `tree`
""" def gerar_estrutura(path=".", prefix=""):
    ignore_dirs = {".git", "__pycache__", "venv", "node_modules", ".idea", ".vscode", ".pytest_cache", "prompts_privados", "temp_storage", "static/imagens"}
    tree = ""
    entries = sorted(os.listdir(path))
    for index, name in enumerate(entries):
        if name in ignore_dirs or name.startswith("."):
            continue
        full_path = os.path.join(path, name)
        connector = "â””â”€â”€ " if index == len(entries) - 1 else "â”œâ”€â”€ "
        tree += f"{prefix}{connector}{name}\n"
        if os.path.isdir(full_path):
            extension = "    " if index == len(entries) - 1 else "â”‚   "
            tree += gerar_estrutura(full_path, prefix + extension)
    return tree """


# 3. Gera resumo tÃ©cnico automÃ¡tico
def gerar_resumo_tecnico():
    return """
## ðŸ”§ Resumo TÃ©cnico


- **ServiÃ§os**: Camada lÃ³gica estÃ¡ em `app/services` (e subpastas).
- **IntegraÃ§Ã£o com LLMs**: Em `app/llm`, com chamadas e prompts dinÃ¢micos via `load_prompt`.
- **Pipeline de dados**: Com etapas modulares em `app/pipeline/scripts`.
- **ChromaDB**: IntegraÃ§Ã£o vetorial em `app/chroma`.
- **Firestore e Imagens**: Em `app/firestore/` e `routes/imagens.py`.
- **Deploy**: AutomaÃ§Ã£o com `Dockerfile`, `.bat` scripts e futura integraÃ§Ã£o contÃ­nua.
"""


# 4. Atualiza o README com a nova estrutura
def atualizar_readme():
    titulo = "# ðŸŒ± Projeto DermaSync\n"
    imagem_arquitetura = "![Arquitetura DermaSync](docs/arquitetura-dermasync.png)\n"
    print("ðŸ“ Atualizando README.md com a nova estrutura...")
    arvore = gerar_estrutura(
        ".",
        ignore_patterns=[
            "*.pyc",  # Ignora arquivos .pyc
            "__pycache__",  # Ignora diretÃ³rio __pycache__
            "venv",  # Ignora diretÃ³rio venv
            ".git",  # Ignora diretÃ³rio .git
            "node_modules",  # Ignora diretÃ³rio node_modules
            "*.log",  # Ignora arquivos de log
            ".pytest_cache",  # Ignora diretÃ³rio de cache do pytest
            ".vscode",  # Ignora diretÃ³rio de configuraÃ§Ã£o do VSCode
            "htmlcov",  # Ignora diretÃ³rio de cobertura HTML
            "prompts_privados",  # Ignora diretÃ³rio de prompts privados
            "temp_storage",  # Ignora diretÃ³rio de armazenamento temporÃ¡rio
            "static",  # Ignora diretÃ³rio de arquivos estÃ¡ticos
            "docs",  # Ignora diretÃ³rio de documentaÃ§Ã£o
            "__init__.py",  # Ignora arquivos __init__.py
            "__main__.py",  # Ignora arquivos __main__.py
            "app.py",  # Ignora o arquivo principal da aplicaÃ§Ã£o
            "main.py",  # Ignora o arquivo principal da aplicaÃ§Ã£o
            "Procfile",  # Ignora o Procfile
            "requirements.txt",  # Ignora o arquivo de requisitos
            "Dockerfile",  # Ignora o Dockerfile
            "README.md",  # Ignora o README.md
            "run_tests.py",  # Ignora o script de execuÃ§Ã£o de testes
            "tree.py",  # Ignora o script de Ã¡rvore de diretÃ³rios
            "atualizar_readme_estrutura.py",  # Ignora o script de atualizaÃ§Ã£o do README
            "firebase_admin_sa.json",  # Ignora o arquivo de credenciais do Firebase
            ".env",  # Ignora o arquivo de variÃ¡veis de ambiente
            ".env.example",  # Ignora o arquivo de exemplo de variÃ¡veis de ambiente
            ".dockerignore",  # Ignora o arquivo .dockerignore
            ".gitignore",  # Ignora o arquivo .gitignore
            "pytest.ini",  # Ignora o arquivo de configuraÃ§Ã£o do pytest
            "alembic.ini",  # Ignora o arquivo de configuraÃ§Ã£o do alembic
            "alembic",  # Ignora o diretÃ³rio do alembic
            "migrations",  # Ignora o diretÃ³rio de migrations
            "instance",  # Ignora o])
        ],
    )
    print(f"ðŸŒ³ Estrutura de pastas gerada com sucesso. {arvore}")
    resumo = gerar_resumo_tecnico()
    print("ðŸ”§ Resumo tÃ©cnico gerado com sucesso.")
    diagrama = gerar_diagrama_mermaid()
    print("ðŸ“Š Diagrama Mermaid gerado com sucesso.")
    imagem_diagrama = None  # Inicializa como None
    # Verifica se o diagrama foi carregado corretamente
    if diagrama:
        imagem_diagrama = (
            carregar_imagem_diagrama()
        )  # Carrega imagem do diagrama se existir
    novo_conteudo = f"""{titulo}

DermaSync Ã© uma API de cÃ³digo aberto para auxiliar no diagnÃ³stico e tratamento de dermatite atÃ³pica, utilizando inteligÃªncia artificial para analisar relatos de pacientes e sugerir soluÃ§Ãµes personalizadas.

## Diagrama Mermaid
{diagrama}
{imagem_diagrama}
## ðŸ“– SumÃ¡rio

{resumo}

## ðŸ“ Estrutura de Pastas
```text
{arvore}
```

## ðŸ“œ Detalhes do Projet
# ðŸŒ± Projeto DermaSync â€“ Estrutura Atualizada
{imagem_arquitetura}
## ðŸ“ AtualizaÃ§Ã£o do README
ðŸ•“ Ãšltima atualizaÃ§Ã£o automÃ¡tica: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""

    README.write_text(novo_conteudo, encoding="utf-8")
    print("README.md atualizado com sucesso.")


def carregar_imagem_diagrama():
    imagem_path = Path("docs/diagram.png")
    if imagem_path.exists():
        return f"![Arquitetura DermaSync]({imagem_path.as_posix()})\n"
    return "âš ï¸ Diagrama visual ainda nÃ£o disponÃ­vel.\n"


def gerar_diagrama_mermaid():
    """
    Gera um diagrama Mermaid a partir do arquivo docs/diagram.mmd.
    """
    mermaid_diagram = carregar_arquivo_mermaid()

    if mermaid_diagram:
        print("Diagrama Mermaid carregado com sucesso.")
        return mermaid_diagram
    else:
        print("âš ï¸ Diagrama Mermaid nÃ£o encontrado ou vazio.")
        return ""


# ExecuÃ§Ã£o principal
if __name__ == "__main__":
    criar_backup()
    atualizar_readme()
