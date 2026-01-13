# app/domain/relato/effects/base.py
from abc import ABC


class Effect(ABC):
    """
    Efeito declarativo emitido pelo domínio.
    Não executa nada.
    """
    pass