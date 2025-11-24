import logging
import uuid
from datetime import datetime, timezone
from typing import Union, List

from fastapi import HTTPException
from app.auth.schemas import User
from app.archlog_sync.logger import registrar_log
from app.firestore.client import get_firestore_client
from app.logger_config import configurar_logger_json
from app.schema.relato import RelatoFullOutput, RelatoPublicoOutput, RelatoCompletoInput
from app.services.imagens_service import get_imagem_by_id, salvar_imagem_from_base64, mark_image_as_orphaned
from app.firestore.persistencia import salvar_relato_firestore

# Para produção (chame uma vez no início do seu main ou serviço)
configurar_logger_json()

logger = logging.getLogger(__name__)

# Define as constantes de status permitidos para relatos
ALLOWED_RELATO_STATUSES = ["novo", "processing", "processed", "approved_public", "rejected", "archived"] # NEW CONSTANT


async def listar_relatos():
    logger.info("Iniciando a listagem de relatos")
    db = get_firestore_client()
    if not db:
        logger.info("Erro ao obter o cliente Firestore")
        raise Exception("Erro ao obter o cliente Firestore")
    try:

        docs = db.collection("relatos").stream()
        resultados = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  # Adiciona o ID do documento
            resultados.append(data)

        logger.info(
            f"Listagem de relatos concluída , total de {len(resultados)} relatos encontrados"
        )

        return resultados

    except Exception as e:
        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")


async def enqueue_relato_processing(relato_id: str):
    """
    (Stub) Adiciona o relato a uma fila para processamento assíncrono (LLM, metadados, anonimização, micro_depoimento).
    """
    logger.info(
        f"Relato {relato_id} enfileirado para processamento em segundo plano."
    )
    # TODO: Implementar integração real com uma fila (Celery, RQ, Cloud Tasks) aqui.
    pass


async def get_relatos_by_owner_id(owner_user_id: str) -> list:
    """
    Lista relatos pertencentes a um usuário específico.
    """
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    try:
        relatos_ref = db.collection("relatos").where("owner_user_id", "==", owner_user_id).stream()
        resultados = []
        for doc in relatos_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            resultados.append(data)
        logger.info(f"Listagem de relatos para owner {owner_user_id} concluída, total de {len(resultados)} relatos encontrados.")
        return resultados
    except Exception as e:
        logger.exception(f"Erro ao listar relatos para owner {owner_user_id}.")
        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")


async def get_relato_by_id(relato_id: str, requesting_user: User) -> Union[RelatoFullOutput, RelatoPublicoOutput]:
    """
    Busca um relato pelo ID com base nas permissões do usuário e status do relato.
    Retorna o documento completo para owner/admin/colaborador ou campos públicos se aprovado publicamente.
    """
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get() # MODIFIED: Removed await

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato não encontrado.")

    relato_data = doc.to_dict()

    is_owner = relato_data.get("owner_user_id") == requesting_user.id
    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]
    is_public = relato_data.get("status") == "approved_public"

    if is_owner or is_admin_or_colab:
        return RelatoFullOutput(**relato_data)
    elif is_public:
        return RelatoPublicoOutput(**relato_data) # This will automatically filter fields
    else:
        raise HTTPException(status_code=403, detail="Acesso negado. Relato privado ou não publicado.")

async def attach_image_to_relato(
    relato_id: str, image_id: str, current_user: User
) -> RelatoFullOutput:
    """
    Anexa um image_id a um relato existente.
    """
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    # 1. Get Relato and check permissions
    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get() # MODIFIED: Removed await

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato não encontrado.")
    
    relato_data = doc.to_dict()
    is_owner = relato_data.get("owner_user_id") == current_user.id
    is_admin_or_colab = current_user.role in ["admin", "colaborador"]

    if not (is_owner or is_admin_or_colab):
        raise HTTPException(status_code=403, detail="Acesso negado. Você não tem permissão para modificar este relato.")

    # 2. Get Image and check permissions
    # Use the existing get_imagem_by_id to check image existence and ownership
    try:
        image_metadata = await get_imagem_by_id(image_id=image_id, requesting_user=current_user)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Imagem não encontrada ou não pertence a você.")
        if e.status_code == 403:
            raise HTTPException(status_code=403, detail="Acesso negado à imagem.")
        raise e # Re-raise other HTTP exceptions

    # Ensure image is not already associated or in a final state
    if image_metadata.get("status") in ["associated", "approved_public", "rejected", "archived"]:
        raise HTTPException(status_code=400, detail="Imagem já associada ou em estado final.")


    # 3. Update Relato's imagens_ids
    imagens_ids = relato_data.get("imagens_ids", {"antes": None, "durante": [], "depois": None})
    
    # Simple logic to add to 'durante' if type isn't specified.
    # A more sophisticated solution would have a specific image_type (antes/durante/depois) in the payload
    if image_id not in imagens_ids["durante"]: # Prevent duplicates
        imagens_ids["durante"].append(image_id)
    
    try:
        await doc_ref.update({"imagens_ids": imagens_ids, "updated_at": datetime.now(timezone.utc)})
        logger.info(f"Imagem {image_id} anexada ao relato {relato_id}.")
        
        # 4. Update Image Status to 'associated'
        image_doc_ref = db.collection("imagens").document(image_id)
        await image_doc_ref.update({"status": "associated", "updated_at": datetime.now(timezone.utc)})
        
        relato_data.update({"imagens_ids": imagens_ids, "updated_at": datetime.now(timezone.utc)})
        return RelatoFullOutput(**relato_data)
    except Exception as e:
        logger.exception(f"Falha ao anexar imagem {image_id} ao relato {relato_id}.")
        raise HTTPException(status_code=500, detail=f"Erro ao anexar imagem: {str(e)}")


async def list_pending_moderation_relatos(requesting_user: User) -> list:
    """
    Lista relatos com status 'processed' aguardando moderação.
    Apenas para usuários com roles 'admin' ou 'colaborador'.
    """
    if requesting_user.role not in ["admin", "colaborador"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores e colaboradores podem listar relatos pendentes de moderação.")

    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    try:
        relatos_ref = db.collection("relatos").where("status", "==", "processed").stream()
        resultados = []
        for doc in relatos_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            resultados.append(data)
        logger.info(f"Listagem de relatos pendentes de moderação concluída, total de {len(resultados)} relatos encontrados.")
        return resultados
    except Exception as e:
        logger.exception("Erro ao listar relatos pendentes de moderação.")
        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")


async def update_relato_status(
    relato_id: str, new_status: str, current_user: User
) -> RelatoFullOutput:
    """
    Atualiza o status de um relato.
    Apenas para usuários com roles 'admin' ou 'colaborador'.
    """
    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores e colaboradores podem alterar o status do relato.")

    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get() # MODIFIED: Removed await

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato não encontrado.")

    relato_data = doc.to_dict()

    # Validate new_status against allowed literals
    if new_status not in ALLOWED_RELATO_STATUSES: # MODIFIED
        raise HTTPException(status_code=400, detail=f"Status inválido: '{new_status}'. Status permitidos: {', '.join(ALLOWED_RELATO_STATUSES)}")

    try:
        await doc_ref.update({"status": new_status, "updated_at": datetime.now(timezone.utc)})
        logger.info(f"Status do relato {relato_id} atualizado para '{new_status}' por {current_user.id}.")
        relato_data["status"] = new_status
        relato_data["updated_at"] = datetime.now(timezone.utc)
        return RelatoFullOutput(**relato_data)
    except Exception as e:
        logger.exception(f"Falha ao atualizar status do relato {relato_id} para '{new_status}'.")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status do relato: {str(e)}")


async def process_and_save_relato(relato: RelatoCompletoInput, current_user: User) -> dict:
    """
    Processa um relato completo, incluindo o salvamento de imagens em base64,
    persiste o relato no Firestore e o enfileira para processamento.
    """
    if not relato.conteudo_original.strip():
        raise HTTPException(status_code=400, detail="Relato não pode estar vazio.")

    logger.info(f"Usuário {current_user.id} enviando relato {relato.id_relato}")

    imagens_ids = {"antes": None, "durante": [], "depois": None}
    uploaded_image_ids = []

    try:
        if relato.imagens.antes:
            metadata = await salvar_imagem_from_base64(
                base64_str=relato.imagens.antes,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_antes.jpg",
            )
            imagens_ids["antes"] = metadata["id"]
            uploaded_image_ids.append(metadata["id"])

        for i, imagem_base64 in enumerate(relato.imagens.durante):
            metadata = await salvar_imagem_from_base64(
                base64_str=imagem_base64,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_durante_{i}.jpg",
            )
            imagens_ids["durante"].append(metadata["id"])
            uploaded_image_ids.append(metadata["id"])

        if relato.imagens.depois:
            metadata = await salvar_imagem_from_base64(
                base64_str=relato.imagens.depois,
                owner_user_id=current_user.id,
                filename=f"{relato.id_relato}_depois.jpg",
            )
            imagens_ids["depois"] = metadata["id"]
            uploaded_image_ids.append(metadata["id"])

    except HTTPException as e:
        logger.error(f"Erro ao processar imagens do relato. Limpando {len(uploaded_image_ids)} imagens parcialmente salvas.")
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao processar imagens do relato. Limpando imagens parcialmente salvas.")
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise HTTPException(status_code=500, detail="Erro ao salvar imagens.")

    doc_relato = {
        "id": uuid.uuid4().hex,
        "id_relato_cliente": relato.id_relato,
        "owner_user_id": current_user.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conteudo_original": relato.conteudo_original,
        "classificacao_etaria": relato.classificacao_etaria,
        "idade": relato.idade,
        "genero": relato.genero,
        "sintomas": relato.sintomas,
        "imagens_ids": imagens_ids,
        "regioes_afetadas": relato.regioes_afetadas,
        "status": "novo",
    }

    try:
        doc_id = salvar_relato_firestore(doc_relato)
        logger.info(f"Relato {doc_id} salvo com sucesso no Firestore.")
        await enqueue_relato_processing(doc_id)
    except Exception as e:
        logger.exception("Erro ao salvar relato no Firestore. Executando rollback das imagens.")
        for img_id in uploaded_image_ids:
            await mark_image_as_orphaned(img_id)
        raise HTTPException(status_code=500, detail="Erro ao persistir o relato.")

    return {
        "status": "sucesso",
        "message": "Relato recebido com sucesso!",
        "relato_id": doc_id,
        "imagens_processadas_ids": imagens_ids,
    }