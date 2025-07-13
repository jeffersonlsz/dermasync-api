# app/routes/imagens.py

"""
Este módulo contém os endpoints da API para gerenciamento de relatos.
"""
import logging
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.archlog_sync.logger import registrar_log
from app.services.imagens_service import listar_imagens, salvar_imagem

router = APIRouter(prefix="/imagens", tags=["Serviços de Imagens"])

logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_imagem(file: UploadFile = File(...)):

    logger.info(f"Recebendo imagem: {file.filename}")

    try:
        start = datetime.now(timezone.utc)
        request_id = uuid4().hex
        url = await salvar_imagem(file)
        end = datetime.now(timezone.utc)
        duration_ms = int((end - start).total_seconds() * 1000)

        logger.info(
            f"Imagem {file.filename} salva com sucesso em {url} - Tempo de processamento: {duration_ms}ms"
        )
        await registrar_log(
            {
                "timestamp": datetime.now(timezone.utc),
                "request_id": request_id,
                "caller": "imagens.py - upload_imagem",
                "callee": "imagens_service",
                "operation": "upload",
                "status_code": 200,
                "duration_ms": duration_ms,
                "details": f"Imagem {file.filename} salva com sucesso",
                "metadata": {"url": url},
            }
        )
        return {"status": "sucesso", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listar-todas")
async def get_imagens() -> List[dict]:
    logger.info("Iniciando a listagem de imagens")
    try:
        start = datetime.now(timezone.utc)
        request_id = uuid4().hex
        imagens = await listar_imagens()
        end = datetime.now(timezone.utc)
        duration_ms = int((end - start).total_seconds() * 1000)

        logger.info(
            f"Listagem de imagens concluída em {duration_ms}ms, total de {len(imagens)} imagens encontradas"
        )

        await registrar_log(
            {
                "timestamp": datetime.now(timezone.utc),
                "request_id": request_id,
                "caller": "get_imagens",
                "callee": "imagens_service",
                "operation": "listar-todas",
                "status_code": 200,
                "duration_ms": duration_ms,
                "details": "imagens.py - get_imagens - listagem de imagens concluída com sucesso",
                "metadata": {"quantidade": len(imagens), "dados": imagens},
            }
        )

        return {"quantidade": len(imagens), "dados": imagens}
    except Exception as e:
        logger.error(f"Erro ao listar imagens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
