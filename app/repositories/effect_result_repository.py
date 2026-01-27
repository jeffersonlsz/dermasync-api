# app/repositories/effect_result_repository.py
from typing import List
from datetime import datetime, timedelta

from google.cloud import firestore

from app.services.effects.result import EffectResult, EffectStatus
"""
⚠️ EffectResultRepository

Este repositório persiste fatos de execução (LEGADO).
Ele NÃO representa UX Effects canônicos.

UX Effects são derivados via adapters
e projeções semânticas.
"""


from app.services.effects.persist_firestore import persist_effect_result_firestore


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
            .order_by("created_at")
        )

        results: List[EffectResult] = []

        for doc in query.stream():
            data = doc.to_dict()

            _metadata = data.get("metadata", {}) or {}
            if "executed_at" in data:
                _metadata["old_executed_at"] = self._parse_datetime(data["executed_at"])
            if "effect_ref" in data:
                _metadata["effect_ref"] = data["effect_ref"]
            if "failure_type" in data:
                _metadata["failure_type"] = data["failure_type"]
            if "retry_decision" in data:
                _metadata["old_retry_decision"] = data["retry_decision"]
            if "retryable" in data:
                _metadata["old_retryable"] = data["retryable"] # Capture legacy retryable field


            # Handle legacy 'success' field if 'status' is not present
            if "status" not in data:
                if bool(data.get("success", False)):
                    status = EffectStatus.SUCCESS
                else:
                    status = EffectStatus.ERROR # Default to ERROR for old failed effects
            else:
                status = EffectStatus(data["status"])

            if status == EffectStatus.SUCCESS:
                results.append(
                    EffectResult.success(
                        relato_id=data["relato_id"],
                        effect_type=data["effect_type"],
                        metadata=_metadata,
                    )
                )
            elif status == EffectStatus.ERROR:
                results.append(
                    EffectResult.error(
                        relato_id=data["relato_id"],
                        effect_type=data["effect_type"],
                        error_message=data.get("error_message", data.get("error", "Unknown error")),
                        metadata=_metadata,
                    )
                )
            elif status == EffectStatus.RETRYING:
                # Firestore stores timedelta as seconds, convert back to timedelta
                retry_after_seconds = data.get("retry_after_seconds")
                retry_after_timedelta = timedelta(seconds=retry_after_seconds) if retry_after_seconds is not None else None
                results.append(
                    EffectResult.retrying(
                        relato_id=data["relato_id"],
                        effect_type=data["effect_type"],
                        retry_after=retry_after_timedelta,
                        metadata=_metadata,
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
        effect_result: EffectResult,
    ) -> None:
        """
        Registra um EffectResult com falha.

        - NÃO lança exceção
        - NÃO contém lógica de domínio
        - Apenas persiste o fato ocorrido
        """
        persist_effect_result_firestore(effect_result)

    
    
    def register_success(
        self,
        effect_result: EffectResult,
    ) -> None:
        """
        Registra um EffectResult bem-sucedido.

        Este é o caminho canônico para efeitos concluídos com sucesso.
        """
        persist_effect_result_firestore(effect_result)
        
    