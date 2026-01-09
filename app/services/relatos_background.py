# app/services/relatos_background.py
"""
Background tasks para processamento de relatos.
Esta camada NÃO deve conter lógica de negócio.
"""
import logging
import uuid
from typing import Optional

from app.domain.relato.contracts import Actor, ActorRole, MarkRelatoAsError, MarkRelatoAsUploaded
from app.domain.relato.orchestrator import decide
from app.domain.relato.states import RelatoStatus
from app.services.relato_adapters import update_relato_status_adapter
from app.services.relato_effect_executor import RelatoEffectExecutor

logger = logging.getLogger(__name__)


def _update_status_domain(relato_id: str, action: str, error_message: Optional[str] = None):
    """
    Função interna para mudar o status de um relato via camada de domínio.
    """
    from app.firestore.client import get_firestore_client
    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error(f"[BG_DOMAIN] Relato {relato_id} não encontrado para atualização de status.")
        return

    current_status_str = doc.to_dict().get("status")
    if not current_status_str:
        logger.error(f"[BG_DOMAIN] Relato {relato_id} não possui status.")
        return
    
    current_status = RelatoStatus(current_status_str)

    command_map = {
        "uploaded": MarkRelatoAsUploaded(relato_id=relato_id),
        "error": MarkRelatoAsError(relato_id=relato_id, error_message=error_message),
    }

    command = command_map.get(action.lower())
    if not command:
        logger.error(f"[BG_DOMAIN] Ação de background desconhecida: {action}")
        return

    actor = Actor(id="system", role=ActorRole.SYSTEM)
    decision = decide(command=command, actor=actor, current_state=current_status)

    if not decision.allowed:
        logger.error(f"[BG_DOMAIN] Transição de estado não permitida para o relato {relato_id}: {decision.reason}")
        return

    executor = RelatoEffectExecutor(
        persist_relato=lambda *a, **k: None,
        enqueue_processing=lambda *a, **k: None,
        emit_event=lambda *a, **k: None,
        upload_images=lambda *a, **k: None,
        update_relato_status=update_relato_status_adapter,
    )
    executor.execute(effects=decision.effects)
    logger.info(f"[BG_DOMAIN] Status do relato {relato_id} alterado para {decision.next_state.value if decision.next_state else 'UNKNOWN'}.")


def _save_files_and_enqueue(
    *,
    relato_id: str,
    owner_id: str,
    imagens_antes: list,
    imagens_durante: list,
    imagens_depois: list,
):
    """
    Processa o upload de imagens em background e atualiza o status do relato via domínio.
    """
    from app.services.imagens_service import salvar_imagem_bytes_to_storage
    from app.services.relatos_service import enqueue_relato_processing

    logger.info(f"[RELATO_BG] Iniciando processamento do relato {relato_id}")
    logger.info(f"[RELATO_BG] Owner ID: {owner_id}")

    try:
        def processar_imagens(imagens: list, papel_clinico: str):
            for file_data in imagens:
                content = file_data
                storage_path = (
                    f"relatos/{relato_id}/{papel_clinico}/"
                    f"{uuid.uuid4().hex}.bin"
                )
                salvar_imagem_bytes_to_storage(storage_path, content)

        processar_imagens(imagens_antes, "ANTES")
        processar_imagens(imagens_durante, "DURANTE")
        processar_imagens(imagens_depois, "DEPOIS")

        # Notifica o domínio que o upload foi concluído
        _update_status_domain(relato_id=relato_id, action="uploaded")

        # Enfileira o próximo passo do processamento
        # Idealmente, isso também seria um comando de domínio que retorna um EnqueueEffect
        enqueue_relato_processing(relato_id=relato_id)

    except Exception as e:
        logger.exception(f"[RELATO_BG] Erro no processamento do relato {relato_id}: {e}")
        _update_status_domain(relato_id=relato_id, action="error", error_message=str(e))

