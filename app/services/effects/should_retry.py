# app/services/effects/should_retry.py
from app.services.effects.result import EffectResult
from app.services.effects.classify_retry import classify_retry


def should_retry(effect: EffectResult) -> bool:
    """
    Camada fina para uso por executores / UX.
    NÃO contém regra.
    NÃO contém heurística.
    """
    decision = classify_retry(effect)
    return decision.should_retry
