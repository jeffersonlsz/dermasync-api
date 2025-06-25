# app/services/imagens_service.py

import uuid
import os
from fastapi import UploadFile
from typing import List
import base64
from uuid import uuid4
from app.firestore.client import get_storage_bucket

PASTA_IMAGENS = "static/imagens"  # Use Firebase depois

# Garante a pasta no início
os.makedirs(PASTA_IMAGENS, exist_ok=True)


def salvar_imagem_base64(base64_str: str, path_no_bucket: str) -> str:
    """
    Recebe uma imagem em base64, salva no Firebase Storage e retorna a URL pública.
    """
    bucket = get_storage_bucket()
    blob = bucket.blob(path_no_bucket)
    blob.upload_from_string(base64.b64decode(base64_str), content_type="image/jpeg")
    blob.make_public()
    return blob.public_url


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

