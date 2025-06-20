import uuid
import os
from fastapi import UploadFile
from typing import List

PASTA_IMAGENS = "static/imagens"  # Use Firebase depois

# Garante a pasta no início
os.makedirs(PASTA_IMAGENS, exist_ok=True)

async def salvar_imagem(file: UploadFile) -> str:
    extensao = file.filename.split(".")[-1]
    nome_arquivo = f"{uuid.uuid4()}.{extensao}"
    caminho = os.path.join(PASTA_IMAGENS, nome_arquivo)
    print(f"Salvando imagem em: {caminho}")
    with open(caminho, "wb") as f:
        conteudo = await file.read()
        f.write(conteudo)
    caminho_absoluto = os.path.abspath(caminho)
    
    print(f"Arquivo salvo localmente em {caminho_absoluto}")
    return f"/{PASTA_IMAGENS}/{nome_arquivo}"

async def listar_imagens() -> List[dict]:
    arquivos = os.listdir(PASTA_IMAGENS)
    return [{"nome": f, "url": f"/{PASTA_IMAGENS}/{f}"} for f in arquivos if not f.startswith(".")]
