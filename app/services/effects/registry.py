# app/services/effects/registry.py

from typing import Callable, Dict

Executor = Callable[[dict], None]

_EFFECT_EXECUTORS: Dict[str, Executor] = {}


def register_effect_executor(effect_type: str, executor: Executor) -> None:
    if not effect_type or not isinstance(effect_type, str):
        raise ValueError("effect_type inválido")

    if not callable(executor):
        raise ValueError("executor deve ser callable")

    _EFFECT_EXECUTORS[effect_type] = executor


def get_effect_executor(effect_type: str) -> Executor | None:
    return _EFFECT_EXECUTORS.get(effect_type)


def clear_registry() -> None:
    _EFFECT_EXECUTORS.clear()


def list_supported_effects() -> set[str]:
    return set(_EFFECT_EXECUTORS.keys())
