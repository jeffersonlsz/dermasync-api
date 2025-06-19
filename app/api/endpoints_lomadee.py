
import logging
from google.cloud import firestore
from fastapi import APIRouter


router = APIRouter()
#1750207048137fb5abe6e
APP_TOKEN = "1750207048137fb5abe6e"
@router.get("/callback")
async def lomadee_callback(codigoTransacao: str = "", anuncianteId: str = ""):
    logging.info(f"Recebido callback: Transacao={codigoTransacao}, Anunciante={anuncianteId}")

    # Salvar no Firestore (exemplo simplificado)
    db = firestore.Client()
    db.collection("logs").document("afiliados").collection("lomadee").add({
        "codigoTransacao": codigoTransacao,
        "anuncianteId": anuncianteId,
        "status": "recebido"
    })

    return {"status": "ok"}