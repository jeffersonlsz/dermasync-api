# app/routes/imagens.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.imagens_service import salvar_imagem, listar_imagens
from typing import List

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
