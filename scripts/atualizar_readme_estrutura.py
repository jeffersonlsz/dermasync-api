import datetime
import os
from pathlib import Path

from tree import print_directory_tree as gerar_estrutura

# Caminho do projeto
ROOT = Path(__file__).parent
print(f"ğŸŒ± Iniciando atualização do README na pasta: {ROOT}")
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
        print("README.md original não encontrado.")


# 1.2 Carrega diagrama Mermaid
def carregar_arquivo_mermaid():
    path = Path("docs/diagram.mmd")
    if path.exists():
        return f"```mermaid\n{path.read_text(encoding='utf-8')}\n```"
    return "âš ï¸ Diagrama em texto (Mermaid) não disponível.\n"


# 2. Gera estrutura de árvore estilo `tree`
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


# 3. Gera resumo técnico automático
def gerar_resumo_tecnico():
    return """
## ğŸ”§ Resumo Técnico


- **Serviços**: Camada lógica está em `app/services` (e subpastas).
- **Integração com LLMs**: Em `app/llm`, com chamadas e prompts dinâmicos via `load_prompt`.
- **Pipeline de dados**: Com etapas modulares em `app/pipeline/scripts`.
- **ChromaDB**: Integração vetorial em `app/chroma`.
- **Firestore e Imagens**: Em `app/firestore/` e `routes/imagens.py`.
- **Deploy**: Automação com `Dockerfile`, `.bat` scripts e futura integração contínua.
"""


# 4. Atualiza o README com a nova estrutura
def atualizar_readme():
    titulo = "# ğŸŒ± Projeto DermaSync\n"
    imagem_arquitetura = "![Arquitetura DermaSync](docs/arquitetura-dermasync.png)\n"
    print("ğŸ“ Atualizando README.md com a nova estrutura...")
    arvore = gerar_estrutura(
        ".",
        ignore_patterns=[
            "*.pyc",  # Ignora arquivos .pyc
            "__pycache__",  # Ignora diretório __pycache__
            "venv",  # Ignora diretório venv
            ".git",  # Ignora diretório .git
            "node_modules",  # Ignora diretório node_modules
            "*.log",  # Ignora arquivos de log
            ".pytest_cache",  # Ignora diretório de cache do pytest
            ".vscode",  # Ignora diretório de configuração do VSCode
            "htmlcov",  # Ignora diretório de cobertura HTML
            "prompts_privados",  # Ignora diretório de prompts privados
            "temp_storage",  # Ignora diretório de armazenamento temporário
            "static",  # Ignora diretório de arquivos estáticos
            "docs",  # Ignora diretório de documentação
            "__init__.py",  # Ignora arquivos __init__.py
            "__main__.py",  # Ignora arquivos __main__.py
            "app.py",  # Ignora o arquivo principal da aplicação
            "main.py",  # Ignora o arquivo principal da aplicação
            "Procfile",  # Ignora o Procfile
            "requirements.txt",  # Ignora o arquivo de requisitos
            "Dockerfile",  # Ignora o Dockerfile
            "README.md",  # Ignora o README.md
            "run_tests.py",  # Ignora o script de execução de testes
            "tree.py",  # Ignora o script de árvore de diretórios
            "atualizar_readme_estrutura.py",  # Ignora o script de atualização do README
            "firebase_admin_sa.json",  # Ignora o arquivo de credenciais do Firebase
            ".env",  # Ignora o arquivo de variáveis de ambiente
            ".env.example",  # Ignora o arquivo de exemplo de variáveis de ambiente
            ".dockerignore",  # Ignora o arquivo .dockerignore
            ".gitignore",  # Ignora o arquivo .gitignore
            "pytest.ini",  # Ignora o arquivo de configuração do pytest
            "alembic.ini",  # Ignora o arquivo de configuração do alembic
            "alembic",  # Ignora o diretório do alembic
            "migrations",  # Ignora o diretório de migrations
            "instance",  # Ignora o])
        ],
    )
    print(f"ğŸŒ³ Estrutura de pastas gerada com sucesso. {arvore}")
    resumo = gerar_resumo_tecnico()
    print("ğŸ”§ Resumo técnico gerado com sucesso.")
    diagrama = gerar_diagrama_mermaid()
    print("ğŸ“Š Diagrama Mermaid gerado com sucesso.")
    imagem_diagrama = None  # Inicializa como None
    # Verifica se o diagrama foi carregado corretamente
    if diagrama:
        imagem_diagrama = (
            carregar_imagem_diagrama()
        )  # Carrega imagem do diagrama se existir
    novo_conteudo = f"""{titulo}

DermaSync é uma API de código aberto para auxiliar no diagnóstico e tratamento de dermatite atópica, utilizando inteligência artificial para analisar relatos de pacientes e sugerir soluções personalizadas.

## Diagrama Mermaid
{diagrama}
{imagem_diagrama}
## ğŸ“– Sumário

{resumo}

## ğŸ“ Estrutura de Pastas
```text
{arvore}
```

## ğŸ“œ Detalhes do Projet
# ğŸŒ± Projeto DermaSync â€“ Estrutura Atualizada
{imagem_arquitetura}
## ğŸ“ Atualização do README
ğŸ•“ Ãšltima atualização automática: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""

    README.write_text(novo_conteudo, encoding="utf-8")
    print("README.md atualizado com sucesso.")


def carregar_imagem_diagrama():
    imagem_path = Path("docs/diagram.png")
    if imagem_path.exists():
        return f"![Arquitetura DermaSync]({imagem_path.as_posix()})\n"
    return "âš ï¸ Diagrama visual ainda não disponível.\n"


def gerar_diagrama_mermaid():
    """
    Gera um diagrama Mermaid a partir do arquivo docs/diagram.mmd.
    """
    mermaid_diagram = carregar_arquivo_mermaid()

    if mermaid_diagram:
        print("Diagrama Mermaid carregado com sucesso.")
        return mermaid_diagram
    else:
        print("âš ï¸ Diagrama Mermaid não encontrado ou vazio.")
        return ""


# Execução principal
if __name__ == "__main__":
    criar_backup()
    atualizar_readme()
