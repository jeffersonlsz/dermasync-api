import logging
import uuid
from datetime import datetime, timezone
from typing import Union, List

import asyncio
from fastapi import HTTPException
from google.cloud import firestore
from google.api_core.exceptions import FailedPrecondition
from google.cloud.firestore import FieldFilter
from app.auth.schemas import User
from app.archlog_sync.logger import registrar_log
from app.firestore.client import get_firestore_client
from app.logger_config import configurar_logger_json
from app.schema.relato import RelatoFullOutput, RelatoPublicoOutput, RelatoCompletoInput, RelatoPublicPreviewDTO, ImagePreviewsDTO
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
        relatos_ref = db.collection("relatos").where(filter=FieldFilter("owner_user_id", "==", owner_user_id)).stream()
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
    doc = await asyncio.to_thread(doc_ref.get)

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato não encontrado.")

    relato_data = doc.to_dict()
    relato_data['id'] = doc.id # Garante que o id do documento está presente

    # --- Camada de Mapeamento e Normalização ---
    # Transforma o 'relato_data' do Firestore para o formato esperado pelos modelos Pydantic
    
    # Converte 'created_at' (string ISO) para datetime, se necessário
    timestamp_str = relato_data.get("created_at") or relato_data.get("timestamp")
    timestamp_dt = None
    if isinstance(timestamp_str, str):
        try:
            # Remove o 'Z' se presente, pois fromisoformat lida melhor com +00:00
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            timestamp_dt = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp_dt = datetime.now(timezone.utc) # Fallback
    elif isinstance(timestamp_str, datetime):
        timestamp_dt = timestamp_str
    else:
        timestamp_dt = datetime.now(timezone.utc) # Fallback

    # Mapeia os campos para o formato do RelatoFullOutput
    mapped_data = {
        "id": relato_data.get("id", doc.id),
        "id_relato_cliente": relato_data.get("id_relato_cliente", relato_data.get("id", doc.id)),
        "owner_user_id": str(relato_data.get("owner_id", relato_data.get("owner_user_id", ""))),
        "timestamp": timestamp_dt,
        "conteudo_original": relato_data.get("meta", {}).get("descricao", relato_data.get("conteudo_original", "")),
        "classificacao_etaria": relato_data.get("classificacao_etaria"),
        "idade": relato_data.get("idade") or relato_data.get("meta", {}).get("idade"),
        "genero": relato_data.get("genero") or relato_data.get("meta", {}).get("sexo"),
        "sintomas": relato_data.get("sintomas", []),
        "imagens_ids": relato_data.get("images", relato_data.get("imagens_ids", {})),
        "regioes_afetadas": relato_data.get("regioes_afetadas", []),
        "status": relato_data.get("status", "unknown"),
        "micro_depoimento": relato_data.get("micro_depoimento"),
        "solucao_encontrada": relato_data.get("solucao_encontrada"),
    }

    # --- Fim da Camada de Mapeamento ---

    is_owner = mapped_data["owner_user_id"] == requesting_user.id
    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]
    is_public = mapped_data["status"] == "approved_public"

    try:
        if is_owner or is_admin_or_colab:
            return RelatoFullOutput(**mapped_data)
        elif is_public:
            return RelatoPublicoOutput(**mapped_data) # Pydantic irá filtrar os campos
        else:
            raise HTTPException(status_code=403, detail="Acesso negado. Relato privado ou não publicado.")
    except Exception as e:
        logger.error(f"Pydantic validation error for relato {relato_id}: {e}")
        logger.error(f"Data passed to Pydantic: {mapped_data}")
        raise HTTPException(status_code=500, detail="Erro de validação de dados internos.")

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
        relatos_ref = db.collection("relatos").where(filter=FieldFilter("status", "==", "processed")).stream()
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
    
async def listar_relatos_publicos_preview(limit: int = 50, status_filter: str = None) -> list:
    """
    Retorna uma lista de relatos formatada para exibição pública (galeria).
    Normaliza documentos legados que usam 'imagens' com URLs e também aceita
    documentos que não tenham 'owner_user_id'.
    """
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    try:
        # Query simples: pega todos e filtramos em python (por compatibilidade com esquemas legados)
        docs = db.collection("relatos").limit(limit).stream()
        resultados = []
        for doc in docs:
            data = doc.to_dict()
            doc_id = doc.id

            # Heurística para decidir se mostramos o relato:
            # Mostrar se:
            #  - tem 'imagens' (legacy) ou 'imagens_ids'
            #  - tem 'microdepoimento' ou 'descricao'
            #  - se status_filter foi passado, respeitar
            if status_filter:
                if str(data.get("status") or "").lower() != str(status_filter).lower():
                    continue

            has_images = bool(data.get("imagens") or data.get("imagens_ids"))
            has_text = bool((data.get("microdepoimento") or data.get("descricao") or "").strip())

            if not (has_images or has_text):
                continue

            # Normalizar saída pública mínima
            safe = {
                "id": data.get("id", doc_id),
                "criado_em": data.get("criado_em") or data.get("timestamp") or None,
                "classificacao": data.get("classificacao") or data.get("classificacao_etaria"),
                "microdepoimento": data.get("microdepoimento") or (data.get("descricao")[:300] if data.get("descricao") else None),
                "tags": data.get("tags_extraidas") or data.get("tags") or [],
                # imagens: se for legacy 'imagens' (URLs) retornamos diretamente; se for imagens_ids,
                # deixamos vazio (frontend vai buscar detalhes via outro endpoint autenticado se necessário)
                "imagens": data.get("imagens") or None,
                "status": data.get("status") or None,
            }
            resultados.append(safe)

        return resultados

    except Exception as e:
        logger.exception("Erro ao listar relatos públicos para galeria.")
        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")
    



async def listar_relatos_publicos_galeria_publica_preview(
    *,
    limit: int,
    page: int,
    only_public: bool = True
) -> List[RelatoPublicPreviewDTO]:
    """
    Lista relatos públicos anonimizados para a galeria pública.

    Retorna apenas relatos com public_visibility.status == "PUBLIC"
    e projeta para RelatoPublicPreviewDTO.
    """
    def sync_get_docs():
        db = get_firestore_client()
        # Use collection_group to query across all 'relatos' subcollections
        query = db.collection_group("relatos")

        # Segurança: só público
        if only_public:
            query = query.where(filter=FieldFilter("public_visibility.status", "==", "PUBLIC"))

        # Ordenação por criação (mais recentes primeiro)
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)

        # Paginação
        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)
        
        docs = query.stream()
        #import pdb
        #pdb.set_trace()
        resultados: List[RelatoPublicPreviewDTO] = []

        for doc in docs:
            data = doc.to_dict()

            # Defesa extrema: nunca confiar no dado
            if not data:
                continue

            public_visibility = data.get("public_visibility", {})
            if public_visibility.get("status") != "PUBLIC":
                continue
            
            public_excerpt = data.get("public_excerpt") or {}

            # Montar previews de imagem
            previews = None
            images = public_excerpt.get("image_previews")

            if isinstance(images, dict):
                before = images.get("before")
                after = images.get("after")

                if before or after:
                    previews = ImagePreviewsDTO(before=before, after=after)

            # created_at defensivo
            created_at_raw = data.get("created_at")
            if isinstance(created_at_raw, str):
                created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            elif isinstance(created_at_raw, datetime):
                created_at = created_at_raw
            else:
                created_at = datetime.now(timezone.utc)
            
            try:
                dto = RelatoPublicPreviewDTO(
                    id=data.get("id") or doc.id,
                    excerpt=public_excerpt.get("text", "")[:120],
                    age_range=public_excerpt.get("age_range"),
                    duration=public_excerpt.get("duration"),
                    tags=public_excerpt.get("tags", []),
                    image_previews=previews,
                    created_at=created_at
                )
                resultados.append(dto)
            except Exception:
                # Ignora relatos com dados inválidos
                pass
        return resultados

    try:
        return await asyncio.to_thread(sync_get_docs)
    except FailedPrecondition as e:
        logger.error(f"Firestore query requires an index: {e.message}")
        raise HTTPException(
            status_code=500,
            detail=f"Query requires a Firestore index. See logs for the creation URL. Error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Erro ao buscar relatos para galeria pública: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching gallery.")
