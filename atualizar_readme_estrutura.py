import os
import datetime
from pathlib import Path
from tree import print_directory_tree as gerar_estrutura
# Caminho do projeto
ROOT = Path(__file__).parent
print(f"🌱 Iniciando atualização do README na pasta: {ROOT}")
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
""" def gerar_estrutura(path=".", prefix=""):
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
    return tree """

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
    print("📝 Atualizando README.md com a nova estrutura...")
    arvore = gerar_estrutura('.', ignore_patterns=[        '*.pyc',        # Ignora arquivos .pyc
        '__pycache__', # Ignora diretório __pycache__

        'venv',         # Ignora diretório venv
        '.git',         # Ignora diretório .git
        'node_modules', # Ignora diretório node_modules
        '*.log',         # Ignora arquivos de log
        '.pytest_cache', # Ignora diretório de cache do pytest
        '.vscode', # Ignora diretório de configuração do VSCode
        'htmlcov', # Ignora diretório de cobertura HTML
        'prompts_privados', # Ignora diretório de prompts privados
        'temp_storage', # Ignora diretório de armazenamento temporário
        'static', # Ignora diretório de arquivos estáticos
        'docs', # Ignora diretório de documentação
        '__init__.py', # Ignora arquivos __init__.py
        '__main__.py', # Ignora arquivos __main__.py
        'app.py', # Ignora o arquivo principal da aplicação
        'main.py', # Ignora o arquivo principal da aplicação
        'Procfile', # Ignora o Procfile
        'requirements.txt', # Ignora o arquivo de requisitos
        'Dockerfile', # Ignora o Dockerfile
        'README.md', # Ignora o README.md
        'run_tests.py', # Ignora o script de execução de testes
        'tree.py', # Ignora o script de árvore de diretórios
        'atualizar_readme_estrutura.py', # Ignora o script de atualização do README
        'firebase_admin_sa.json', # Ignora o arquivo de credenciais do Firebase
        '.env', # Ignora o arquivo de variáveis de ambiente
        '.env.example', # Ignora o arquivo de exemplo de variáveis de ambiente
        '.dockerignore', # Ignora o arquivo .dockerignore
        '.gitignore', # Ignora o arquivo .gitignore
        'pytest.ini', # Ignora o arquivo de configuração do pytest
        'alembic.ini', # Ignora o arquivo de configuração do alembic
        'alembic', # Ignora o diretório do alembic
        'migrations', # Ignora o diretório de migrations
        'instance', # Ignora o])
    ])
    print(f"🌳 Estrutura de pastas gerada com sucesso. {arvore}")
    resumo = gerar_resumo_tecnico()

    novo_conteudo = f"""{titulo}

## 📁 Estrutura de Pastas
```text
{arvore}
```
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
