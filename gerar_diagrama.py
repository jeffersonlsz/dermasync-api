import typer
from app.observabilidade.log_parser import carregar_logs, agrupar_por_request_id
from app.observabilidade.mermaid_generator import gerar_mermaid
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Comando principal do Typer
app = typer.Typer()

@app.command()
def generate(input: str):
    logger.info(f"Iniciando geração de diagramas a partir do arquivo: {input}")
    logs = carregar_logs(input)
    logger.info(f"{len(logs)} logs carregados do arquivo {input}")
    fluxos = agrupar_por_request_id(logs)

    for req_id, fluxo in fluxos.items():
        gerar_mermaid(fluxo, nome_arquivo=f"outputs/fluxo_{req_id}.mmd")

if __name__ == "__main__":
    app()