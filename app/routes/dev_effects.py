from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User
from app.services.dev_effect_injector_service import DevEffectInjectorService

router = APIRouter(
    prefix="/dev",
    tags=["DEV - Effects"],
)


@router.post(
    "/relatos/{relato_id}/mock-effect",
    status_code=status.HTTP_201_CREATED,
)
def create_mock_effect(
    relato_id: str,
    effect_type: str,
    success: bool = True,
    user: User = Depends(get_current_user),
):
    """
    Cria um EffectResult mockado diretamente no Firestore.

    Uso típico:
    - effect_type=ENRICH_METADATA
    - success=true
    """

    # ⚠️ IMPORTANTE
    # Aqui você pode (opcionalmente) restringir:
    # if user.role != "admin": raise HTTPException(403)

    try:
        service = DevEffectInjectorService()
        service.inject_effect(
            relato_id=relato_id,
            effect_type=effect_type,
            success=success,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao injetar effect mock",
        ) from exc

    return {
        "relato_id": relato_id,
        "effect_type": effect_type,
        "success": success,
        "status": "mock effect criado",
    }
