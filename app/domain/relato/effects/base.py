# app/domain/relato/effects/base.py
from abc import ABC


class Effect(ABC):
    """
    Efeito declarativo emitido pelo domnio.
    No executa nada.
    """
    pass
