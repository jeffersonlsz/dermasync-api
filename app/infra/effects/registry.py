# app/infra/effects/registry.py
from typing import Callable, Dict, Protocol


class EffectExecutor(Protocol):
    def __call__(self, effect: dict) -> None: ...


_EFFECT_EXECUTORS: Dict[str, EffectExecutor] = {}


def register(effect_type: str, executor: EffectExecutor) -> None:
    if not effect_type:
        raise ValueError("effect_type inválido")

    _EFFECT_EXECUTORS[effect_type] = executor


def resolve(effect_type: str) -> EffectExecutor | None:
    return _EFFECT_EXECUTORS.get(effect_type)


def clear() -> None:
    _EFFECT_EXECUTORS.clear()


def supported_effects() -> set[str]:
    return set(_EFFECT_EXECUTORS.keys())
