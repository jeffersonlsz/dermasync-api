# app/services/galeria_service.py
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.cloud.firestore import FieldFilter

from app.domain.galeria.eligibility_service import RelatoEligibilityService
from app.domain.galeria.similarity.calculator import SimilarityCalculator
from app.firestore.client import get_firestore_client
from app.services.imagens_service import _generate_signed_url_sync
from app.services.relato_normalizer import normalize_relato_document
from app.services.ux_adapters.galeria_explanation import GaleriaExplanationBuilder


from google.cloud.firestore import FieldFilter



# ============================================================
# ðŸ”¹ SeleÃ§Ã£o de thumbnails (ANTES / DEPOIS)
# ============================================================

def _pick_thumbnails(imagens: List[dict]) -> Dict[str, str | None]:
    """
    Retorna thumbnails separadas por papel clÃ­nico.
    Prioridade:
      - ANTES
      - DEPOIS
    """
    thumbs = {
        "antes": None,
        "depois": None,
    }

    for img in imagens:
        papel = img.get("papel_clinico")
        thumb_path = img.get("storage", {}).get("thumb_path")

        if not thumb_path:
            continue

        if papel == "ANTES" and thumbs["antes"] is None:
            thumbs["antes"] = _generate_signed_url_sync(thumb_path)

        elif papel == "DEPOIS" and thumbs["depois"] is None:
            thumbs["depois"] = _generate_signed_url_sync(thumb_path)

    return thumbs

# ============================================================
# ðŸ§  ServiÃ§os Cognitivos (legacy-safe)
# ============================================================

_eligibility_service = RelatoEligibilityService()
_similarity_calculator = SimilarityCalculator()
_explanation_builder = GaleriaExplanationBuilder()

# ============================================================
# ðŸŒ Galeria PÃºblica v3 (batch, otimizado)
# ============================================================

async def listar_galeria_publica_v3(
    *,
    limit: int,
    page: int
) -> Dict[str, Any]:

    db = get_firestore_client()

    # ============================================================
    # ðŸ§  ServiÃ§os Cognitivos (legacy-safe)
    # ============================================================
    from app.domain.galeria.eligibility_service import RelatoEligibilityService
    from app.domain.galeria.visibility_policy import (
        RelatoVisibilityPolicy,
        RelatoStatus,
    )
    from app.services.ux_adapters.galeria_explanation import (
        GaleriaExplanationBuilder,
    )

    eligibility_service = RelatoEligibilityService()
    explanation_builder = GaleriaExplanationBuilder()

    # --------------------------------------------------------
    # 1ï¸âƒ£ Buscar relatos pÃºblicos
    # --------------------------------------------------------
    relatos_query = (
        db.collection_group("relatos")
        .where(filter=FieldFilter("public_visibility.status", "==", "PUBLIC"))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .offset((page - 1) * limit)
    )

    relatos = await asyncio.to_thread(
        lambda: [(doc.id, doc.to_dict()) for doc in relatos_query.stream()]
    )

    if not relatos:
        return {
            "meta": {
                "page": page,
                "limit": limit,
                "count": 0
            },
            "dados": []
        }

    relato_ids = [relato_id for relato_id, _ in relatos]

    # --------------------------------------------------------
    # 2ï¸âƒ£ Buscar imagens em batch
    # --------------------------------------------------------
    imagens_query = (
        db.collection("imagens")
        .where(filter=FieldFilter("relato_id", "in", relato_ids))
        .where(filter=FieldFilter("status.visibilidade", "==", "public"))
        .where(filter=FieldFilter("status.moderacao", "==", "approved"))
    )

    imagens_raw = await asyncio.to_thread(
        lambda: [doc.to_dict() for doc in imagens_query.stream()]
    )

    imagens_por_relato: Dict[str, List[dict]] = {}
    for img in imagens_raw:
        imagens_por_relato.setdefault(img["relato_id"], []).append(img)

    # --------------------------------------------------------
    # 3ï¸âƒ£ Montar resposta final (D2 ATIVO)
    # --------------------------------------------------------
    dados: List[Dict[str, Any]] = []

    for relato_id, relato in relatos:
        imagens = imagens_por_relato.get(relato_id, [])

        thumbs = _pick_thumbnails(imagens)

        thumbnail_url = (
            thumbs["antes"]
            or thumbs["depois"]
            or None
        )

        created_at_raw = relato.get("created_at")
        if isinstance(created_at_raw, str):
            created_at = created_at_raw
        else:
            created_at = datetime.now(timezone.utc).isoformat()

        # =====================================================
        # ðŸ§  PIPELINE COGNITIVO â€” D2 (exposiÃ§Ã£o progressiva)
        # =====================================================

        # PolÃ­tica mÃ­nima (nÃ£o muda comportamento)
        visibility_policy = RelatoVisibilityPolicy(
            status=RelatoStatus.APPROVED,
            constraints=set(),
        )

        eligibility_decision = eligibility_service.decide(
            user=None,  # galeria pÃºblica
            relato_policy=visibility_policy,
        )

        # ðŸ”¹ Similaridade neutra (placeholder controlado)
        similarity_score_value = 0.65

        ux_effects = []

        # explicaÃ§Ã£o base (D)
        ux_effects.extend(
            explanation_builder.build_for_relato(
                eligibility=eligibility_decision,
                similarity=None,
            )
        )

        # exposiÃ§Ã£o progressiva (D2)
        ux_effects.append(
            explanation_builder.build_progressive_exposure(
                similarity_score=similarity_score_value
            )
        )
        from app.services.ux_serializer import serialize_ux_effects

       
        # ----------------------------------------------------
        # Payload final (formatado para o frontend Vue)
        # ----------------------------------------------------
        excerpt = (relato.get("public_excerpt", {}).get("text") or "")[:120]

        dados.append({
            "id": relato_id,
            "tituloRelato": "Relato de tratamento",
            "imgAntes": thumbs.get("antes"),
            "imgDepois": thumbs.get("depois") or thumbs.get("antes"),
            "microdepoimento": excerpt,
            "solucao": excerpt,
            "tags": relato.get("tags_extraidas") or relato.get("tags") or [],
            "created_at": created_at,
            "has_images": bool(imagens),
            "ux_effects": [
                 effect.serialize() if hasattr(effect, "serialize") else effect.__dict__
                 for effect in ux_effects
            ],
        })

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(dados)
        },
        "dados": dados
    }
    
async def listar_galeria_contextual(
    *,
    user_id: str,
    limit: int,
    page: int,
) -> Dict[str, Any]:

    db = get_firestore_client()

    # ============================================================
    # ðŸ§  ServiÃ§os Cognitivos
    # ============================================================
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
    from app.services.ux_adapters.galeria_explanation import (
        GaleriaExplanationBuilder,
    )

    eligibility_service = RelatoEligibilityService()
    similarity_calculator = SimilarityCalculator()
    explanation_builder = GaleriaExplanationBuilder()

    # ============================================================
    # 1ï¸âƒ£ Resolver perfil cognitivo do usuÃ¡rio
    # ============================================================

    # ðŸ”¹ STUB CONTROLADO (v1)
    # Futuro: buscar do Firestore / users / relatos
    user_profile = UserCognitiveProfile(
        user_id=user_id,
        role=UserRole.USER,
        relato_base_id="RELATO_BASE_ID_DO_USUARIO",
        exposure_level=ExposureLevel.BALANCED,
    )

    # ============================================================
    # 2ï¸âƒ£ Buscar relatos candidatos (pÃºblicos)
    # ============================================================

    relatos_query = (
        db.collection_group("relatos")
        .where(filter=FieldFilter("public_visibility.status", "==", "PUBLIC"))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit * 3)  # overfetch controlado
        .offset((page - 1) * limit)
    )

    relatos = await asyncio.to_thread(
        lambda: [(doc.id, doc.to_dict()) for doc in relatos_query.stream()]
    )

    if not relatos:
        return {
            "meta": {
                "page": page,
                "limit": limit,
                "count": 0,
            },
            "dados": [],
        }

    # ============================================================
    # 3ï¸âƒ£ AvaliaÃ§Ã£o cognitiva por relato
    # ============================================================

    scored_relatos = []

    for relato_id, relato in relatos:

        # PolÃ­tica mÃ­nima do relato
        visibility_policy = RelatoVisibilityPolicy(
            status=RelatoStatus.APPROVED,
            constraints={VisibilityConstraint.REQUIRE_SIMILARITY},
        )

        eligibility = eligibility_service.decide(
            user=user_profile,
            relato_policy=visibility_policy,
        )

        if not eligibility.eligible:
            continue

        # --------------------------------------------------------
        # ðŸ”¹ Similaridade v1 (simples e honesta)
        # --------------------------------------------------------

        # STUB: partial scores simples
        partial_scores = {
            # exemplos: substituir depois por lÃ³gica real
            # SimilarityAxis.SYMPTOMS: 0.7,
            # SimilarityAxis.BODY_REGION: 0.6,
        }

        similarity_score = similarity_calculator.calculate(
            partial_scores=partial_scores,
            policy=SIMILARITY_POLICY_V1,
        )

        if eligibility.similarity_required:
            if similarity_score.total < eligibility.min_similarity:
                continue

        scored_relatos.append(
            (relato_id, relato, similarity_score)
        )

    # ============================================================
    # 4ï¸âƒ£ Ordenar por similaridade
    # ============================================================

    scored_relatos.sort(
        key=lambda item: item[2].total,
        reverse=True,
    )

    scored_relatos = scored_relatos[:limit]

    # ============================================================
    # 5ï¸âƒ£ Montar resposta + D2
    # ============================================================

    dados = []

    for relato_id, relato, similarity_score in scored_relatos:

        created_at_raw = relato.get("created_at")
        if isinstance(created_at_raw, str):
            created_at = created_at_raw
        else:
            created_at = datetime.now(timezone.utc).isoformat()

        ux_effects = []

        ux_effects.extend(
            explanation_builder.build_for_relato(
                eligibility=eligibility_service.decide(
                    user=user_profile,
                    relato_policy=RelatoVisibilityPolicy(
                        status=RelatoStatus.APPROVED,
                        constraints=set(),
                    ),
                ),
                similarity=similarity_score,
            )
        )

        ux_effects.append(
            explanation_builder.build_progressive_exposure(
                similarity_score=similarity_score.total
            )
        )

        dados.append({
            "id": relato_id,
            "excerpt": (relato.get("public_excerpt", {}).get("text") or "")[:160],
            "tags": relato.get("tags_extraidas") or [],
            "created_at": created_at,

            "similarity_score": similarity_score.total,

            "ux_effects": [
                effect.serialize() for effect in ux_effects
            ],
        })

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(dados),
        },
        "dados": dados,
    }
    
    
async def resolve_relato_base_for_user(
    *,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Resolve o relato-base cognitivo do usuÃ¡rio.

    PolÃ­tica v1 (congelada):
    - relato mais recente
    - status aprovado
    - com tags_extraidas
    - usado como Ã¢ncora de similaridade

    Retorna apenas os campos necessÃ¡rios para o pipeline cognitivo.
    """

    db = get_firestore_client()
    user_id_str = str(user_id)
    query = (
        db.collection_group("relatos")
        .where(filter=FieldFilter("user_id", "==", user_id_str))
        .where(filter=FieldFilter("status", "==", "approved"))
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
    )

    relatos = await asyncio.to_thread(
        lambda: [doc.to_dict() for doc in query.stream()]
    )

    if not relatos:
        return None

    relato = relatos[0]
    relato = normalize_relato_document(relato)
    
    if not relato:
        return None
    
    tags = relato.get("tags_extraidas") or []
    if not tags:
        return None
    # TODO revisar se isso estÃ¡ correto depois. 
    public_excerpt_field = relato.get("public_excerpt")

    if isinstance(public_excerpt_field, dict):
        excerpt = public_excerpt_field.get("text") or ""
    elif isinstance(public_excerpt_field, str):
        excerpt = public_excerpt_field
    else:
        excerpt = ""

    return {
        "id": relato.get('id'),
        "tags_extraidas": tags,
        "excerpt": excerpt,
    }


