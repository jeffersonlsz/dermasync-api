from datetime import datetime, timezone

import pytest

from app.application.queries.feed_query import FeedService
from app.auth.schemas import User


def _relato(relato_id: str, **overrides):
    data = {
        "id": relato_id,
        "owner_id": "user_123",
        "created_at": datetime.now(timezone.utc),
        "conteudo_original": "texto base do relato " * 20,
        "classificacao_etaria": "30-39",
        "idade": "34",
        "genero": "F",
        "sintomas": ["coceira"],
        "image_refs": {
            "antes": "https://cdn.test/antes.jpg",
            "depois": "https://cdn.test/depois.jpg",
        },
        "regioes_afetadas": ["rosto"],
        "status": "approved",
        "public_visibility": {"status": "PUBLIC"},
        "micro_depoimento": None,
    }
    data.update(overrides)
    return data


class FakeRelatoRepository:
    def __init__(self):
        self.public_relatos = [_relato("rel_1"), _relato("rel_2")]
        self.owner_relatos = [_relato("own_1")]

    def list_public_candidates(self, limit=50):
        return self.public_relatos[:limit]

    def list_owner_relatos(self, owner_user_id: str, limit=5):
        return self.owner_relatos[:limit]


class ReverseIdRankingPolicy:
    def score(self, user, relato):
        return 1.0 if relato.id == "rel_2" else 0.1


@pytest.mark.asyncio
async def test_feed_anonimo_retorna_preview_publico_com_imagens():
    service = FeedService(FakeRelatoRepository())

    feed = await service.get_feed(None, page=1, limit=12)

    assert len(feed) == 2
    assert feed[0].type == "relato_preview"
    assert feed[0].id == "rel_1"
    assert len(feed[0].excerpt) <= 120
    assert feed[0].image_previews.antes == ["https://cdn.test/antes.jpg"]
    assert feed[0].image_previews.depois == ["https://cdn.test/depois.jpg"]


@pytest.mark.asyncio
async def test_feed_usuario_logado_nao_quebra_e_prioriza_relato_do_usuario():
    service = FeedService(FakeRelatoRepository())
    user = User(
        id="user_123",
        firebase_uid="fb_user_123",
        role="usuario_logado",
        idade_aprox=34,
        principais_areas_pele=["rosto"],
    )

    feed = await service.get_feed(user, page=1, limit=12)

    assert [item.id for item in feed][:1] == ["own_1"]
    assert all(item.image_previews.depois for item in feed)


@pytest.mark.asyncio
async def test_feed_usuario_logado_usa_politica_de_ranking_injetada():
    repo = FakeRelatoRepository()
    repo.owner_relatos = []
    service = FeedService(repo, ranking_policy=ReverseIdRankingPolicy())
    user = User(
        id="user_123",
        firebase_uid="fb_user_123",
        role="usuario_logado",
    )

    feed = await service.get_feed(user, page=1, limit=12)

    assert [item.id for item in feed] == ["rel_2", "rel_1"]


@pytest.mark.asyncio
async def test_feed_admin_nao_quebra():
    service = FeedService(FakeRelatoRepository())
    user = User(
        id="admin_001",
        firebase_uid="fb_admin_001",
        role="admin",
    )

    feed = await service.get_feed(user, page=1, limit=12)

    assert [item.id for item in feed] == ["rel_1", "rel_2"]


@pytest.mark.asyncio
async def test_feed_limita_paginacao_defensivamente_no_service():
    service = FeedService(FakeRelatoRepository())

    feed = await service.get_feed(None, page=0, limit=1000)

    assert len(feed) == 2


@pytest.mark.asyncio
async def test_feed_nao_exibe_relato_com_public_visibility_privada_mesmo_aprovado():
    repo = FakeRelatoRepository()
    repo.public_relatos = [
        _relato(
            "private_approved",
            status="approved",
            public_visibility={"status": "PRIVATE"},
        ),
        _relato("public_approved"),
    ]
    service = FeedService(repo)

    feed = await service.get_feed(None, page=1, limit=12)

    assert [item.id for item in feed] == ["public_approved"]


@pytest.mark.asyncio
async def test_feed_mantem_fallback_legado_quando_public_visibility_nao_existe():
    repo = FakeRelatoRepository()
    legacy = _relato("legacy_approved", status="approved")
    legacy.pop("public_visibility")
    repo.public_relatos = [legacy]
    service = FeedService(repo)

    feed = await service.get_feed(None, page=1, limit=12)

    assert [item.id for item in feed] == ["legacy_approved"]


@pytest.mark.asyncio
async def test_feed_normaliza_documento_legado_antes_do_dto_publico():
    repo = FakeRelatoRepository()
    repo.public_relatos = [
        {
            "id": "legacy_shape",
            "owner_user_id": "user_123",
            "timestamp": "2026-05-20T10:00:00Z",
            "content": "texto legado completo",
            "meta": {"idade": "34", "sexo": "F", "classificacao": "30-39"},
            "public_excerpt": {
                "text": "resumo publico legado",
                "age_range": "30-39",
                "tags": ["legado", "pele"],
                "image_previews": {
                    "before": "https://cdn.test/before.jpg",
                    "after": "https://cdn.test/after.jpg",
                },
            },
            "status": "approved",
            "public_visibility": {"status": "PUBLIC"},
        }
    ]
    service = FeedService(repo)

    feed = await service.get_feed(None, page=1, limit=12)

    assert len(feed) == 1
    assert feed[0].id == "legacy_shape"
    assert feed[0].excerpt == "resumo publico legado"
    assert feed[0].age_range == "30-39"
    assert feed[0].tags == ["legado", "pele"]
    assert feed[0].image_previews.antes == ["https://cdn.test/before.jpg"]
    assert feed[0].image_previews.depois == ["https://cdn.test/after.jpg"]
