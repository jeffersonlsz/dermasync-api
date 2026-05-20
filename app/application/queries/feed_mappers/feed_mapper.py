from app.schema.relato import (
    ImagePreviewsDTO,
    RelatoFullOutput,
    RelatoPublicPreviewDTO,
)


def _preview_list(value):
    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]


def relato_full_to_preview(
    relato: RelatoFullOutput,
    hide_after: bool = False,
) -> RelatoPublicPreviewDTO:
    excerpt = (relato.micro_depoimento or relato.conteudo_original or "")[:120]

    previews = None
    if relato.image_refs:
        after = None if hide_after else relato.image_refs.get("depois")
        previews = ImagePreviewsDTO(
            antes=_preview_list(relato.image_refs.get("antes")),
            depois=_preview_list(after),
        )

    return RelatoPublicPreviewDTO(
        id=relato.id,
        excerpt=excerpt,
        age_range=relato.classificacao_etaria,
        tags=relato.sintomas or [],
        image_previews=previews,
        created_at=relato.created_at,
    )
