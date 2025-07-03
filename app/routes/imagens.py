# app/routes/imagens.py

"""
Este módulo contém os endpoints da API para gerenciamento de relatos.
"""

from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.imagens_service import listar_imagens, salvar_imagem

router = APIRouter(prefix="/imagens", tags=["Serviços de Imagens"])


@router.post("/upload")
async def upload_imagem(file: UploadFile = File(...)):
    try:
        url = await salvar_imagem(file)
        return {"status": "sucesso", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listar-todas")
async def get_imagens() -> List[dict]:
    return await listar_imagens()
