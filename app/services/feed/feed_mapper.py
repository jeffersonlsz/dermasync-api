# app/services/feed/feed_mapper.py
from app.schema.relato import RelatoFullOutput, RelatoPublicPreviewDTO, ImagePreviewsDTO


def relato_full_to_preview(relato: RelatoFullOutput) -> RelatoPublicPreviewDTO:

    excerpt = relato.micro_depoimento or relato.conteudo_original[:120]

    previews = None

    if relato.image_refs:
        previews = ImagePreviewsDTO(
            before=relato.image_refs.get("antes"),
            after=relato.image_refs.get("depois")
        )

    return RelatoPublicPreviewDTO(
        id=relato.id,
        excerpt=excerpt,
        age_range=relato.classificacao_etaria,
        tags=relato.sintomas or [],
        image_previews=previews,
        created_at=relato.created_at
    )
