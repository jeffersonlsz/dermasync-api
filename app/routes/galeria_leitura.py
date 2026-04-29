# app/routes/galeria_leitura.py
# Endpoint de leitura mediada de relatos na galeria pÃºblica.

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_optional_user
from app.auth.schemas import User
from app.firestore.client import get_firestore_client

from app.services.galeria_service import resolve_relato_base_for_user
from app.services.relato_normalizer import normalize_relato_document
from app.services.ux_adapters.galeria_explanation import (
    GaleriaExplanationBuilder,
)

from app.domain.galeria.user_profile import (
    UserCognitiveProfile,
    UserRole,
    ExposureLevel,
)
from app.domain.galeria.eligibility_service import RelatoEligibilityService
from app.domain.galeria.visibility_policy import (
    RelatoVisibilityPolicy,
    RelatoStatus,
    VisibilityConstraint,
)
from app.domain.galeria.similarity.calculator import SimilarityCalculator
from app.domain.galeria.similarity.policy import SIMILARITY_POLICY_V1
from app.domain.galeria.similarity.axes import SimilarityAxis
from app.domain.galeria.similarity.scorers.tags_overlap import (
    jaccard_similarity,
)
from app.domain.galeria.similarity.scorers.narrative_tone import (
    narrative_tone_similarity,
)

from app.services.image_exposure_projector import ImageExposureProjector
from app.services.imagens_service import _generate_signed_url_sync


router = APIRouter()
logger = logging.getLogger(__name__)

image_projector = ImageExposureProjector()

@router.get(
    "/galeria-publica/relatos/{relato_id}/leitura",
    summary="Leitura mediada de um relato",
    tags=["Galeria PÃºblica"],
)
async def ler_relato(
    relato_id: str,
    intent: str = "read",
    current_user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:

    db = get_firestore_client()

    eligibility_service = RelatoEligibilityService()
    similarity_calculator = SimilarityCalculator()
    explanation_builder = GaleriaExplanationBuilder()

    # ============================================================
    # 1ï¸âƒ£ Resolver leitor
    # ============================================================
    user_profile: Optional[UserCognitiveProfile] = None
    relato_base: Optional[Dict[str, Any]] = None

    if current_user:
        relato_base = await resolve_relato_base_for_user(
            user_id=current_user.id
        )

        if not relato_base:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Para ler relatos semelhantes, Ã© necessÃ¡rio que vocÃª tenha enviado um relato.",
            )

        user_profile = UserCognitiveProfile(
            user_id=current_user.id,
            role=UserRole.USER,
            relato_base_id=relato_base["id"],
            exposure_level=ExposureLevel.BALANCED,
        )

    # ============================================================
    # 2ï¸âƒ£ Carregar relato alvo
    # ============================================================
    relato_ref = (
        db.collection_group("relatos")
        .where("id", "==", relato_id)
        .limit(1)
    )

    docs = list(relato_ref.stream())

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Relato nÃ£o encontrado",
        )

    relato = docs[0].to_dict()
    relato = normalize_relato_document(relato)

    # ============================================================
    # 3ï¸âƒ£ Elegibilidade
    # ============================================================
    constraints = set()

    if not user_profile:
        constraints.add(VisibilityConstraint.REQUIRE_SIMILARITY)

    visibility_policy = RelatoVisibilityPolicy(
        status=RelatoStatus.APPROVED,
        constraints=constraints,
    )

    eligibility = eligibility_service.decide(
        user=user_profile,
        relato_policy=visibility_policy,
    )

    if not eligibility.eligible:
        effects = explanation_builder.build_for_relato(
            eligibility=eligibility,
            similarity=None,
        )

        return {
            "relato_id": relato_id,
            "context": None,
            "exposure": {
                "stage": "summary",
                "can_request_more": False,
                "reason": eligibility.reason,
            },
            "content": {
                "excerpt": None,
                "full_text": None,
                "images": images,
                "meta": None,
            },
            "ux_effects": [e.serialize() for e in effects],
        }

    # ============================================================
    # 4ï¸âƒ£ Similaridade
    # ============================================================
    similarity_score = None
    similarity_context = None

    if user_profile and relato_base:

        partial_scores = {
            SimilarityAxis.SYMPTOMS: jaccard_similarity(
                relato_base["tags_extraidas"],
                relato.get("tags_extraidas") or [],
            ),
            SimilarityAxis.THERAPY_RESPONSE: jaccard_similarity(
                relato_base["tags_extraidas"],
                relato.get("tags_extraidas") or [],
            ),
            SimilarityAxis.NARRATIVE_TONE: narrative_tone_similarity(
                relato_base["excerpt"],
                relato.get("public_excerpt", {}).get("text") or "",
            ),
        }

        similarity_score = similarity_calculator.calculate(
            partial_scores=partial_scores,
            policy=SIMILARITY_POLICY_V1,
        )

        similarity_context = {
            "score": similarity_score.total,
            "percentage": round(similarity_score.total * 100),
            "threshold": eligibility.min_similarity,
            "above_threshold": (
                similarity_score.total >= eligibility.min_similarity
                if eligibility.similarity_required
                else True
            ),
        }

     # ============================================================
    # 5ï¸âƒ£ Resolver ExposureStage (controla o que serÃ¡ exibido)
    # ============================================================

    if similarity_score and eligibility.similarity_required:
        if similarity_score.total >= eligibility.min_similarity:
            exposure_stage = "partial"
            can_request_more = True
        else:
            exposure_stage = "summary"
            can_request_more = False
    else:
        exposure_stage = "full"
        can_request_more = False

    # ============================================================
    # ðŸ”“ Intent: expand (liberaÃ§Ã£o explÃ­cita do usuÃ¡rio)
    # ============================================================

    if intent == "expand" and exposure_stage == "partial" and can_request_more:
        exposure_stage = "full"
        can_request_more = False

        expand_effect = {
            "type": "content_expanded",
            "severity": "info",
            "message": "ConteÃºdo completo liberado para visualizaÃ§Ã£o."
        }
    else:
        expand_effect = None

    # ============================================================
    # 6ï¸âƒ£ Projetar conteÃºdo conforme stage
    # ============================================================

    excerpt = relato.get("public_excerpt", {}).get("text") or ""
    full_text_raw = (
        relato.get("conteudo_original")
        or relato.get(" conteudo_anonimizado")
        or ""
    )

    # ðŸ”¹ Texto
    if exposure_stage == "summary":
        full_text = None
        visible_length = 0

    elif exposure_stage == "partial":
        full_text = full_text_raw[:600]
        visible_length = min(600, len(full_text_raw))

    else:  # full
        full_text = full_text_raw
        visible_length = len(full_text_raw)

    # ðŸ”¹ Imagens (jÃ¡ estruturadas como dict com type + path)
    image_refs = relato.get("image_refs") or []
    total_images = len(image_refs)

    if exposure_stage == "summary":
        visible_images = []

    elif exposure_stage == "partial":
        visible_images = image_refs[:1]

    else:
        visible_images = image_refs

    # gerar signed URLs apenas para visÃ­veis
    from app.services.imagens_service import _generate_signed_url_sync

    images = []
    for img in visible_images:
        images.append({
            "type": img.get("type"),
            "url": _generate_signed_url_sync(img.get("path")),
        })

    # ============================================================
    # 7ï¸âƒ£ Montar resposta final
    # ============================================================

    response = {
        "relato_id": relato_id,
        "context": {
            "viewer": {
                "role": user_profile.role.value if user_profile else "anonymous",
                "exposure_level": user_profile.exposure_level.value if user_profile else None,
            },
            "similarity": (
                {
                    "score": similarity_score.total,
                    "percentage": int(similarity_score.total * 100),
                    "threshold": eligibility.min_similarity,
                    "above_threshold": similarity_score.total >= eligibility.min_similarity,
                }
                if similarity_score and eligibility.similarity_required
                else None
            ),
        },
        "exposure": {
            "stage": exposure_stage,
            "can_request_more": can_request_more,
            "reason": eligibility.reason,
        },
        "content": {
            "excerpt": excerpt,
            "full_text": full_text,
            "images": images,
            "images_meta": {
                "total": total_images,
                "visible": len(images),
                "hidden": max(0, total_images - len(images)),
            },
            "meta": {
                "full_length": len(full_text_raw),
                "visible_length": visible_length,
                "truncated": exposure_stage != "full",
            },
        },
        "ux_effects": [],
    }

    if expand_effect:
        response["ux_effects"].append(expand_effect)

    return response

