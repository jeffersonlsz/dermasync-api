from app.domain.relato.contracts import Actor, ActorRole, CreateRelato
from app.domain.relato.effects import PersistImageRefsEffect
from app.domain.relato.orchestrator import decide


def test_create_relato_emits_persist_image_refs_effect():
    decision = decide(
        command=CreateRelato(
            relato_id="relato-123",
            owner_id="user-123",
            conteudo="Relato com imagens",
            image_refs={"antes": ["img-1"], "durante": [], "depois": []},
        ),
        actor=Actor(id="user-123", role=ActorRole.USER),
        current_state=None,
    )

    assert any(isinstance(effect, PersistImageRefsEffect) for effect in decision.effects)
