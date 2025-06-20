from fastapi import APIRouter, HTTPException
from app.services.relatos_service import listar_relatos

router = APIRouter(prefix="/relatos", tags=["Relatos"])

@router.get("/listar-todos")
async def get_relatos():
    try:
        relatos = await listar_relatos()
        return {"quantidade": len(relatos), "dados": relatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
