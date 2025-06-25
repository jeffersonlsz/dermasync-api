# app/routes/relatos.py
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser
from app.schema.relato import RelatoCompletoInput
from app.services.relatos_service import listar_relatos
import json 
from app.firestore.persistencia import salvar_relato_firestore
from app.services.imagens_service import salvar_imagem_base64

router = APIRouter(prefix="/relatos", tags=["Relatos"])

@router.get("/listar-todos")
async def get_relatos():
    try:
        relatos = await listar_relatos()
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
    imagens_processadas = {
        "antes": None,
        "durante": [],
        "depois": None
    }

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
        "regioes_afetadas": relato.regioes_afetadas
    }

    # Salvar no Firestore
    doc_id = salvar_relato_firestore(doc)

    return {
        "status": "sucesso",
        "id": doc["id"],
        "imagens": imagens_processadas,
        "document_id": doc_id  # Retorna o ID do documento salvo
    }
    