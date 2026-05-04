# app/services/relatos_service.py

print("LEGACY SERVICE EXECUTANDO")
import logging

import uuid

import json

from datetime import datetime, timezone

from typing import Union, List



import asyncio

from fastapi import HTTPException, status

from google.cloud import firestore

from google.api_core.exceptions import FailedPrecondition

from google.cloud.firestore import FieldFilter

from app.domain.relato.contracts import ApproveRelatoPublic, RejectRelato, ArchiveRelato

from app.domain.relato.states import RelatoStatus

from app.services.relato_adapters import update_relato_status_adapter

from app.auth.schemas import User

from app.archlog_sync.logger import registrar_log

from app.firestore.client import get_firestore_client

from app.logger_config import configurar_logger_json

from app.schema.relato import RelatoFullOutput, RelatoPublicoOutput, RelatoCompletoInput, RelatoPublicPreviewDTO, ImagePreviewsDTO

from app.schema.relato_draft import RelatoDraftInput

from app.services.imagens_service import get_imagem_by_id, salvar_imagem_from_base64, mark_image_as_orphaned

from app.firestore.persistencia import salvar_relato_firestore

from app.services.relato_effect_executor import RelatoEffectExecutor









# Para produo (chame uma vez no incio do seu main ou servio)

configurar_logger_json()



logger = logging.getLogger(__name__)





async def listar_relatos():
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso ListarRelatosUseCase. Verifique app/application/relatos/listar_relatos_use_case.py para a implementação atualizada.")
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

            f"Listagem de relatos concluda , total de {len(resultados)} relatos encontrados"

        )



        return resultados

    except Exception as e:

        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")

async def enqueue_relato_processing(relato_id: str):
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso SubmitRelatoUseCase. Verifique app/application/relatos/submit_relato_use_case.py para a implementação atualizada.")
    """

    (Stub) Adiciona o relato a uma fila para processamento assncrono (LLM, metadados, anonimizao, micro_depoimento).

    """

    logger.info(

        f"Relato {relato_id} enfileirado para processamento em segundo plano."

    )

    # TODO: Implementar integrao real com uma fila (Celery, RQ, Cloud Tasks) aqui.

    pass





async def get_relatos_by_owner_id(owner_user_id: str) -> list:
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso GetRelatoUseCase. Verifique app/application/relatos/get_relato_use_case.py para a implementação atualizada.")
    """

    Lista relatos pertencentes a um usurio especfico.

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

        logger.info(f"Listagem de relatos para owner {owner_user_id} concluda, total de {len(resultados)} relatos encontrados.")

        return resultados

    except Exception as e:

        logger.exception(f"Erro ao listar relatos para owner {owner_user_id}.")

        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")





async def get_relato_by_id(relato_id: str, requesting_user: User) -> Union[RelatoFullOutput, RelatoPublicoOutput]:
    
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso GetRelatoUseCase. Verifique app/application/relatos/get_relato_use_case.py para a implementação atualizada.")
    """

    Busca um relato pelo ID com base nas permisses do usurio e status do relato.

    Retorna o documento completo para owner/admin/colaborador ou campos pblicos se aprovado publicamente.

    """

    db = get_firestore_client()

    if not db:

        logger.error("Erro ao obter o cliente Firestore")

        raise HTTPException(status_code=500, detail="Erro interno no servidor.")



    doc_ref = db.collection("relatos").document(relato_id)

    doc = await asyncio.to_thread(doc_ref.get)



    if not doc.exists:

        raise HTTPException(status_code=404, detail="Relato no encontrado.")



    relato_data = doc.to_dict()

    relato_data['id'] = doc.id # Garante que o id do documento est presente



    # --- Camada de Mapeamento e Normalizao ---

    # Transforma o 'relato_data' do Firestore para o formato esperado pelos modelos Pydantic

    

    # Converte 'created_at' (string ISO) para datetime, se necessrio

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

        "owner_id": str(relato_data.get("owner_id", relato_data.get("owner_user_id", ""))),

        "timestamp": timestamp_dt,

        "conteudo_original": relato_data.get("meta", {}).get("descricao", relato_data.get("conteudo_original", "")),

        "classificacao_etaria": relato_data.get("classificacao_etaria"),

        "idade": relato_data.get("idade") or relato_data.get("meta", {}).get("idade"),

        "genero": relato_data.get("genero") or relato_data.get("meta", {}).get("sexo"),

        "sintomas": relato_data.get("sintomas", []),

        "image_refs": relato_data.get("images", relato_data.get("imagens_ids", {})),

        "regioes_afetadas": relato_data.get("regioes_afetadas", []),

        "status": relato_data.get("status", "unknown"),

        "micro_depoimento": relato_data.get("micro_depoimento"),

        "solucao_encontrada": relato_data.get("solucao_encontrada"),

        "created_at": relato_data.get("created_at") or timestamp_dt,

    }



    # --- Fim da Camada de Mapeamento ---



    is_owner = mapped_data["owner_id"] == str(requesting_user.id)

    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]

    is_public = mapped_data["status"] == "approved_public"



    try:

        if is_owner or is_admin_or_colab:

            return RelatoFullOutput(**mapped_data)

        elif is_public:

            return RelatoPublicoOutput(**mapped_data) # Pydantic ir filtrar os campos

        else:

            raise HTTPException(status_code=403, detail="Acesso negado. Relato privado ou no publicado.")

    except Exception as e:

        logger.error(f"Pydantic validation error for relato {relato_id}: {e}")

        logger.error(f"Data passed to Pydantic: {mapped_data}")

        raise HTTPException(status_code=500, detail="Erro de validao de dados internos.")



async def attach_image_to_relato(

    relato_id: str, image_id: str, current_user: User

) -> RelatoFullOutput:
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso GetRelatoUseCase. Verifique app/application/relatos/get_relato_use_case.py para a implementação atualizada.")
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

        raise HTTPException(status_code=404, detail="Relato no encontrado.")

    

    relato_data = doc.to_dict()

    is_owner = relato_data.get("owner_user_id") == current_user.id

    is_admin_or_colab = current_user.role in ["admin", "colaborador"]



    if not (is_owner or is_admin_or_colab):

        raise HTTPException(status_code=403, detail="Acesso negado. Voc no tem permisso para modificar este relato.")



    # 2. Get Image and check permissions

    # Use the existing get_imagem_by_id to check image existence and ownership

    try:

        image_metadata = await get_imagem_by_id(image_id=image_id, requesting_user=current_user)

    except HTTPException as e:

        if e.status_code == 404:

            raise HTTPException(status_code=404, detail="Imagem no encontrada ou no pertence a voc.")

        if e.status_code == 403:

            raise HTTPException(status_code=403, detail="Acesso negado à imagem.")

        raise e # Re-raise other HTTP exceptions



    # Ensure image is not already associated or in a final state

    if image_metadata.get("status") in ["associated", "approved_public", "rejected", "archived"]:

        raise HTTPException(status_code=400, detail="Imagem j associada ou em estado final.")





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
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso ListarRelatosPendentesModeracaoUseCase. Verifique app/application/relatos/listar_relatos_pendentes_moderacao_use_case.py para a implementação atualizada.")
    """

    Lista relatos com status 'processed' aguardando moderao.

    Apenas para usurios com roles 'admin' ou 'colaborador'.

    """

    if requesting_user.role not in ["admin", "colaborador"]:

        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores e colaboradores podem listar relatos pendentes de moderao.")



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

        logger.info(f"Listagem de relatos pendentes de moderao concluda, total de {len(resultados)} relatos encontrados.")

        return resultados

    except Exception as e:

        logger.exception("Erro ao listar relatos pendentes de moderao.")

        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")










from app.domain.relato.orchestrator import decide

from app.domain.relato.contracts import Actor, CreateRelato

from app.services.relato_effect_executor import RelatoEffectExecutor

from app.services.relato_adapters import (

    persist_relato_adapter,

    enqueue_processing_adapter,

    emit_event_adapter,

    upload_images_adapter,

)





async def process_and_save_relato(

    relato: RelatoCompletoInput,

    current_user: User,

) -> dict:
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso CreateRelatoUseCase. Verifique app/application/relatos/create_relato_use_case.py para a implementação atualizada.")
    """

    Entrada HTTP para criao de relato.

    NÃO decide regras de domnio.

    """



    # 1️⃣ Validao mnima de contrato HTTP

    if not relato.conteudo_original.strip():

        raise HTTPException(status_code=400, detail="Relato no pode estar vazio.")



    # 2️⃣ Construo do Comando de domnio

    relato_id = uuid.uuid4().hex

    command = CreateRelato(

        relato_id=relato_id,

        owner_id=current_user.id,

        conteudo=relato.conteudo_original,

        imagens={

            "antes": relato.imagens.antes,

            "durante": relato.imagens.durante,

            "depois": relato.imagens.depois,

        },

    )



    actor = Actor(

        id=current_user.id,

        role=current_user.role,

    )



    # 3️⃣ Deciso de domnio

    decision = decide(command=command, actor=actor, current_state=None)



    if not decision.allowed:

        raise HTTPException(status_code=400, detail=decision.reason)



    # 4️⃣ Execuo tcnica dos efeitos

    # Em um cenrio real, as dependncias seriam injetadas

    executor = RelatoEffectExecutor(

        persist_relato=persist_relato_adapter,

        enqueue_processing=enqueue_processing_adapter,

        emit_event=emit_event_adapter,

        upload_images=upload_images_adapter,

        update_relato_status=update_relato_status_adapter,

    )



    executor.execute(effects=decision.effects)



    # 5️⃣ Resposta HTTP

    return {

        "status": "sucesso",

        "message": "Relato recebido com sucesso.",

        "relato_id": relato_id,

    }



    

async def listar_relatos_publicos_preview(limit: int = 50, status_filter: str = None) -> list:
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso ListarRelatosPublicosUseCase. Verifique app/application/relatos/listar_relatos_publicos_use_case.py para a implementação atualizada.")
    """

    Retorna uma lista de relatos formatada para exibio pblica (galeria).

    Normaliza documentos legados que usam 'imagens' com URLs e tambm aceita

    documentos que no tenham 'owner_user_id'.

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



            # Heurstica para decidir se mostramos o relato:

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



            # Normalizar sada pblica mnima

            safe = {

                "id": data.get("id", doc_id),

                "criado_em": data.get("criado_em") or data.get("timestamp") or None,

                "classificacao": data.get("classificacao") or data.get("classificacao_etaria"),

                "microdepoimento": data.get("microdepoimento") or (data.get("descricao")[:300] if data.get("descricao") else None),

                "tags": data.get("tags_extraidas") or data.get("tags") or [],

                # imagens: se for legacy 'imagens' (URLs) retornamos diretamente; se for imagens_ids,

                # deixamos vazio (frontend vai buscar detalhes via outro endpoint autenticado se necessrio)

                "imagens": data.get("imagens") or None,

                "status": data.get("status") or None,

            }

            resultados.append(safe)



        return resultados



    except Exception as e:

        logger.exception("Erro ao listar relatos pblicos para galeria.")

        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")

    

def run_submission_effects(effects: list, executor: RelatoEffectExecutor):
    raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso SubmitRelatoUseCase. Verifique app/application/relatos/submit_relato_use_case.py para a implementação atualizada.")
    """Executa os efeitos da submisso em background."""

    try:

        executor.execute(effects)

    except Exception as e:

        logger.error(f"Erro ao executar efeitos da submisso em background: {e}", exc_info=True)



