from app.domain.relato_status import RelatoStatus


def is_owner(actor_id: str, relato: dict) -> bool:
    return actor_id == relato.get("owner_id")


def can_upload_files(state: RelatoStatus, actor_id: str, relato: dict) -> bool:
    return (
        state == RelatoStatus.UPLOADING
        and is_owner(actor_id, relato)
    )


def can_start_processing(state: RelatoStatus, actor_id: str, relato: dict) -> bool:
    return (
        state == RelatoStatus.UPLOADED
        and is_owner(actor_id, relato)
    )


def can_fail_relato(state: RelatoStatus, actor_id: str, relato: dict) -> bool:
    # erro pode ocorrer em qualquer estado não terminal
    return state not in {RelatoStatus.ERROR, RelatoStatus.DONE}
