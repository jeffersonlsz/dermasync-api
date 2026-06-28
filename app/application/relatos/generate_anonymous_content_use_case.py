# app/application/relatos/generate_anonymous_content_use_case.py
from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
from app.llm.anonymous_content_runner import generate_anonymous_content
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository


class GenerateAnonymousContentUseCase:

    def __init__(
        self,
        relato_repo: FirestoreRelatoRepository,
    ):
        self.relato_repo = relato_repo
        self.enrichment_repo = EnrichedMetadataRepository()

    async def execute(
        self,
        relato_id: str,
    ) -> dict:

        relato = await self.relato_repo.get_by_id(relato_id)

        if relato is None:
            raise ValueError(
                f"Relato '{relato_id}' não encontrado."
            )

        metadados = dict(
            relato.get("metadados", {})
        )

        enrichment = self.enrichment_repo.get(
            relato_id=relato_id
        )

        payload = {
            "metadados": metadados,
            "enrichment": {}
        }

        if enrichment:
            payload["enrichment"] = enrichment.get(
                "data",
                {}
            )

        conteudo_anonimizado = await generate_anonymous_content(
            payload
        )

        await self.relato_repo.update_conteudo_anonimizado(
            relato_id=relato_id,
            conteudo=conteudo_anonimizado,
        )

        return {
            "relato_id": relato_id,
            "conteudo_anonimizado": conteudo_anonimizado,
        }