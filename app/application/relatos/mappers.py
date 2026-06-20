"""
Mappers para transformação de dados de Relatos na camada de Aplicação.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import HTTPException, status
from app.schema.relato_draft import RelatoDraftInput
from app.schema.relato import RelatoPublicPreviewDTO, ImagePreviewsDTO

logger = logging.getLogger(__name__)

def parse_payload_json(payload: str) -> "RelatoDraftInput":
    try:
        data = json.loads(payload)
        return RelatoDraftInput(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

def extract_canonical_relato(data: dict, doc_id: str) -> dict:
    """
    Extrai e resolve o contrato interno canônico de um relato a partir de diferentes
    formatos (legado ou moderno).
    """
    timestamp_raw = data.get("created_at") or data.get("timestamp") or data.get("criado_em")
    if isinstance(timestamp_raw, str):
        try:
            timestamp_dt = datetime.fromisoformat(timestamp_raw.replace('Z', '+00:00'))
        except ValueError:
            timestamp_dt = datetime.now(timezone.utc)
    elif isinstance(timestamp_raw, datetime):
        timestamp_dt = timestamp_raw
    else:
        timestamp_dt = datetime.now(timezone.utc)

    owner_id = str(data.get("owner_id") or data.get("owner_user_id") or "")
    content = data.get("content") or data.get("conteudo_original") or data.get("meta", {}).get("descricao") or data.get("descricao") or data.get("micro_depoimento") or data.get("microdepoimento") or ""
    image_refs = data.get("image_refs") or data.get("images") or data.get("imagens_ids") or data.get("imagens") or {}
    status_val = data.get("status") or "unknown"
    
    return {
        "id": data.get("id", doc_id),
        "owner_id": owner_id,
        "content": content,
        "image_refs": image_refs,
        "created_at": timestamp_dt,
        "status": status_val,
    }

def map_relato_data(relato_data: dict, doc_id: str) -> dict:
    """
    Mapeia dados brutos do Firestore para o modelo interno rico usado pela aplicação.
    """
    canonical = extract_canonical_relato(relato_data, doc_id)
    
    mapped = {
        **relato_data,
        **canonical,
        "id_relato_cliente": relato_data.get("id_relato_cliente", canonical["id"]),
        "timestamp": canonical["created_at"],
        "conteudo_original": canonical["content"],
        "classificacao_etaria": relato_data.get("classificacao_etaria"),
        "idade": relato_data.get("idade") or relato_data.get("meta", {}).get("idade"),
        "genero": relato_data.get("genero") or relato_data.get("meta", {}).get("sexo"),
        "sintomas": relato_data.get("sintomas", []),
        "regioes_afetadas": relato_data.get("regioes_afetadas", []),
        "micro_depoimento": relato_data.get("micro_depoimento"),
        "solucao_encontrada": relato_data.get("solucao_encontrada"),
    }
    return mapped



def map_public_preview_dto(data: dict, doc_id: str) -> Optional[RelatoPublicPreviewDTO]:
    """
    Transforma um relato do Firestore em um DTO de Preview Público para a Galeria.
    """
    canonical = extract_canonical_relato(data, doc_id)
    if not data:
        return None

    meta = data.get("metadados") or {}
    
    obj = RelatoPublicPreviewDTO(
            id=data.get("id", doc_id),
            owner_id=canonical["owner_id"],
            excerpt=data.get("conteudo_original", "")[:120],
            conteudo_original=data.get("conteudo_original"),
            age_range="0-0",
            genero=meta.get("genero") or "sem gênero",
            tags=meta.get("regioes_afetadas") or [],
            image_previews=data.get("image_refs") or {},
            created_at=canonical["created_at"],
            
        )
    
    return obj

