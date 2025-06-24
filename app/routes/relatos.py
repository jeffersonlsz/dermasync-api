from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthUser
from app.schema.relato import RelatoCompletoInput
from app.services.relatos_service import listar_relatos

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

    # Validação extra se quiser
    if not relato.relato_texto.strip():
        raise HTTPException(status_code=400, detail="Relato não pode estar vazio.")

    # Simulação de upload de imagens (depois integraremos Firebase Storage real)
    imagens_urls = []
    for i, imagem in enumerate(relato.imagens):
        nome_arquivo = f"{relato.nome_arquivo}_{i}_{uuid4().hex[:8]}.jpg"
        path = Path(f"./temp_storage/{nome_arquivo}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(imagem)  # simulação de escrita da imagem (base64 como texto)

        imagens_urls.append(str(path))  # depois substitui com URL do Storage

    # Criação do documento persistente (mockado)
    doc = {
        "id": uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "relato_texto": relato.relato_texto,
        "idade": relato.idade_aproximada,
        "genero": relato.genero,
        "sintomas": relato.sintomas,
        "imagens_urls": imagens_urls,
        "regioes_afetadas": relato.regioes_afetadas
    }

    # Por enquanto, simula persistência
    Path("./app/pipeline/dados/relatos_recebidos.jsonl").parent.mkdir(parents=True, exist_ok=True)
    with open("./app/pipeline/dados/relatos_recebidos.jsonl", "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    return {"status": "sucesso", "id": doc["id"], "imagens": imagens_urls}
    