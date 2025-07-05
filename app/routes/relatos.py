# app/routes/relatos.py

"""
Este módulo contém os endpoints da API para gerenciamento de relatos.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.archlog_sync.logger import registrar_log
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser
from app.firestore.persistencia import salvar_relato_firestore
from app.schema.relato import RelatoCompletoInput
from app.services.imagens_service import salvar_imagem_base64
from app.services.relatos_service import listar_relatos

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/relatos", tags=["Relatos"])


@router.get("/listar-todos")
async def get_relatos():
    logger.info("Iniciando a listagem de relatos")
    try:
        start = datetime.now(timezone.utc)
        request_id = uuid4().hex
        relatos = await listar_relatos()
        end = datetime.now(timezone.utc)
        logger.info(
            f"Listagem de relatos concluída em {int((end - start).total_seconds() * 1000)}, total de {len(relatos)} relatos encontrados"
        )
        # Registrar log de listagem de relatos
        await registrar_log(
            {
                "timestamp": datetime.now(timezone.utc),
                "request_id": request_id,
                "caller": "get_relatos",
                "callee": "relatos_service",
                "operation": "listar-todos",
                "status_code": 200,
                "duration_ms": int((end - start).total_seconds() * 1000),
                "details": "relatos.py - get_relatos - listagem de relatos concluída com sucesso",
                "metadata": {"quantidade": len(relatos), "dados": relatos},
            }
        )

        return {"quantidade": len(relatos), "dados": relatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enviar-relato-completo")
async def enviar_relato(relato: RelatoCompletoInput):
    # Validação do schema já é feita automaticamente pelo Pydantic

    # Validação extra do conteúdo
    if not relato.conteudo_original.strip():
        raise HTTPException(status_code=400, detail="Relato não pode estar vazio.")

    # Processamento das imagens (adaptado para o novo schema)
    imagens_processadas = {"antes": None, "durante": [], "depois": None}

    # Upload imagem 'antes'
    if relato.imagens.antes:
        nome = f"{relato.id_relato}/antes_{uuid4().hex[:8]}.jpg"
        url = salvar_imagem_base64(relato.imagens.antes, nome)
        imagens_processadas["antes"] = url

    # Upload imagens 'durante'
    for i, imagem_base64 in enumerate(relato.imagens.durante):
        nome = f"{relato.id_relato}/durante_{i}_{uuid4().hex[:8]}.jpg"
        url = salvar_imagem_base64(imagem_base64, nome)
        imagens_processadas["durante"].append(url)

    # Upload imagem 'depois'
    if relato.imagens.depois:
        nome = f"{relato.id_relato}/depois_{uuid4().hex[:8]}.jpg"
        url = salvar_imagem_base64(relato.imagens.depois, nome)
        imagens_processadas["depois"] = url

    # Criação do documento persistente
    doc = {
        "id": uuid4().hex,
        "id_relato": relato.id_relato,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conteudo_original": relato.conteudo_original,
        "classificacao_etaria": relato.classificacao_etaria,
        "idade": relato.idade,
        "genero": relato.genero,
        "sintomas": relato.sintomas,
        "imagens": imagens_processadas,
        "regioes_afetadas": relato.regioes_afetadas,
    }
    start = datetime.now(timezone.utc)
    request_id = uuid4().hex
    # Salvar no Firestore
    doc_id = salvar_relato_firestore(doc)
    end = datetime.now(timezone.utc)
    duration_ms = int((end - start).total_seconds() * 1000)
    logger.info(f"Relato salvo com sucesso, ID: {doc_id}, duração: {duration_ms} ms")
    # Registrar log de envio de relato
    await registrar_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "caller": "enviar_relato",
            "callee": "POST relatos/enviar-relato-completo",
            "operation": "enviar_relato_completo",
            "status_code": 200,
            "duration_ms": duration_ms,
            "details": "relatos.py - enviar_relato - relato salvo com sucesso",
            "metadata": {
                "id_relato": relato.id_relato,
                "imagens_processadas": imagens_processadas,
                "document_id": doc_id,
            },
        }
    )

    return {
        "status": "sucesso",
        "id": doc["id"],
        "imagens": imagens_processadas,
        "document_id": doc_id,  # Retorna o ID do documento salvo
    }
