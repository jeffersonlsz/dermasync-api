# tests/services/test_executor_idempotency.py

def test_executor_skips_effect_if_already_succeeded(monkeypatch):
    """
    Prova que o executor NÃO executa novamente
    um efeito que já possui EffectResult success=True.
    """

    from app.application.effects.relato_executor import RelatoEffectExecutor
    from app.domain.relato.effects import UploadImagesEffect

    # -----------------------------
    # Controle de chamadas
    # -----------------------------
    upload_call_count = 0

    def fake_upload(relato_id, imagens):
        nonlocal upload_call_count
        upload_call_count += 1
        return ["img-1", "img-2"]

    # -----------------------------
    # Simula idempotência ativa
    # -----------------------------
    def fake_effect_already_succeeded(*, relato_id, effect_type, effect_ref):
        # Simula que o efeito JÃ FOI executado com sucesso
        return True

    monkeypatch.setattr(
        "app.application.effects.relato_executor.effect_already_succeeded",
        fake_effect_already_succeeded,
    )


    # -----------------------------
    # Executor real
    # -----------------------------
    executor = RelatoEffectExecutor(
        upload_images=fake_upload,
        rollback_images=None,
        persist_relato=lambda **_: None,
        enqueue_processing=lambda *_: None,
        emit_event=lambda *_: None,
        update_relato_status=lambda *_: None,
    )

    effects = [
        UploadImagesEffect(
            relato_id="relato-123",
            image_refs={"antes": [], "durante": [], "depois": []},
        )
    ]

    # -----------------------------
    # Execução
    # -----------------------------
    executor.execute(effects)

    # -----------------------------
    # Assertiva CRÃTICA
    # -----------------------------
    assert upload_call_count == 0, (
        "Upload NÃO deveria ser chamado se o efeito "
        "já foi executado com sucesso anteriormente"
    )
