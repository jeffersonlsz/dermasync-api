# app/services/effects/should_retry.py
from app.application.effects.result import EffectResult
from app.application.effects.classify_retry import classify_retry


def should_retry(effect: EffectResult) -> bool:
    """
    Camada fina para uso por executores / UX.
    NÃO contm regra.
    NÃO contm heurstica.
    """
    decision = classify_retry(effect)
    return decision.should_retry
