# app/repositories/effect_result_repository.py
from typing import List
from datetime import datetime

from google.cloud import firestore

from app.domain.ux_progress.progress_aggregator import EffectResult


class EffectResultRepository:
    COLLECTION = "effect_results"
    """
    Repository de leitura de EffectResult (Firestore).

    Responsabilidades:
    - Buscar documentos por relato_id
    - Converter Firestore -> EffectResult
    - NÃO conter lógica de domínio
    """

    def __init__(self, firestore_client: firestore.Client | None = None):
        self._db = firestore_client or firestore.Client()

    def fetch_by_relato_id(self, relato_id: str) -> List[EffectResult]:
        """
        Retorna todos os EffectResult associados a um relato.
        """

        query = (
            self._db.collection("effect_results")
            .where("relato_id", "==", relato_id)
            .order_by("executed_at")
        )

        results: List[EffectResult] = []

        for doc in query.stream():
            data = doc.to_dict()

            results.append(
                EffectResult(
                    type=data["effect_type"],
                    success=bool(data.get("success", False)),
                    executed_at=self._parse_datetime(data["executed_at"]),
                    error_message=data.get("error"),
                )
            )

        return results

    @staticmethod
    def _parse_datetime(value) -> datetime:
        """
        Converte timestamp do Firestore para datetime Python.
        """
        if isinstance(value, datetime):
            return value

        # Caso venha como string ISO
        if isinstance(value, str):
            return datetime.fromisoformat(value)

        # Caso venha como Timestamp do Firestore
        return value.to_datetime()
    
    
    def register_failure(
        self,
        relato_id: str,
        effect_type: str,
        error: str,
        retryable: bool = False,
        metadata: dict | None = None,
    ) -> None:
        """
        Registra um EffectResult com falha.

        - NÃO lança exceção
        - NÃO contém lógica de domínio
        - Apenas persiste o fato ocorrido
        """

        doc = {
            "relato_id": relato_id,
            "effect_type": effect_type,
            "success": False,
            "executed_at": datetime.utcnow(),
            "error": error,
            "retryable": retryable,
            "metadata": metadata or {},
        }

        self._db.collection(self.COLLECTION).add(doc)

    
    
    def register_success(
        self,
        relato_id: str,
        effect_type: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Registra um EffectResult bem-sucedido.

        Este é o caminho canônico para efeitos concluídos com sucesso.
        """

        doc = {
            "relato_id": relato_id,
            "effect_type": effect_type,
            "success": True,
            "executed_at": datetime.utcnow(),
            "metadata": metadata or {},
        }

        self._db.collection(self.COLLECTION).add(doc)
        
    