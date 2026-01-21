# app/services/dev_effect_injector_service.py
from datetime import datetime
from typing import Optional

from google.cloud import firestore


class DevEffectInjectorService:
    """
    Serviço DEV para injetar EffectResult diretamente na base.

    ATENÇÃO:
    - Uso exclusivo para desenvolvimento / testes
    - Não contém lógica de domínio
    - Não executa efeitos reais
    """

    def __init__(self, firestore_client: firestore.Client | None = None):
        self._db = firestore_client or firestore.Client()

    def inject_effect(
        self,
        relato_id: str,
        effect_type: str,
        success: bool = True,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Insere um EffectResult artificial no Firestore.
        """

        doc = {
            "relato_id": relato_id,
            "effect_type": effect_type,
            "success": success,
            "executed_at": datetime.utcnow(),
            "metadata": metadata or {
                "mock": True,
                "source": "dev",
            },
        }

        self._db.collection("effect_results").add(doc)
