"""

Module queries.py.

"""



import logging

import asyncio

from typing import Union, List

from fastapi import HTTPException

from google.api_core.exceptions import FailedPrecondition

from google.cloud.firestore_v1.base_query import FieldFilter, Or



from app.auth.schemas import User

from app.firestore.client import get_firestore_client

from app.schema.relato import RelatoFullOutput, RelatoPublicoOutput, RelatoPublicPreviewDTO

from .mappers import map_relato_data, map_public_preview_dto

from .legacy_normalizer import normalize_public_preview



logger = logging.getLogger(__name__)



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

            data["id"] = doc.id

            resultados.append(data)

        logger.info(f"Listagem de relatos concluda , total de {len(resultados)} relatos encontrados")

        return resultados

    except Exception as e:

        raise Exception(f"Erro ao acessar o Firestore: {str(e)}")



async def get_relatos_by_owner_id(owner_user_id: str) -> list:

    db = get_firestore_client()

    if not db:

        logger.error("Erro ao obter o cliente Firestore")

        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    try:

        filter_1 = FieldFilter("owner_user_id", "==", owner_user_id)

        filter_2 = FieldFilter("owner_id", "==", owner_user_id)

        combined_filter = Or([filter_1, filter_2])

        

        relatos_ref = db.collection("relatos").where(filter=combined_filter).stream()

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
    db = get_firestore_client()

    if not db:

        logger.error("Erro ao obter o cliente Firestore")

        raise HTTPException(status_code=500, detail="Erro interno no servidor.")



    doc_ref = db.collection("relatos").document(relato_id)

    doc = await asyncio.to_thread(doc_ref.get)



    if not doc.exists:

        raise HTTPException(status_code=404, detail="Relato no encontrado.")



    relato_data = doc.to_dict()

    relato_data['id'] = doc.id



    mapped_data = map_relato_data(relato_data, doc.id)



    is_owner = mapped_data["owner_id"] == str(requesting_user.id)

    is_admin_or_colab = requesting_user.role in ["admin", "colaborador"]

    is_public = mapped_data["status"] == "approved_public"



    try:

        if is_owner or is_admin_or_colab:

            return RelatoFullOutput(**mapped_data)

        elif is_public:

            return RelatoPublicoOutput(**mapped_data)

        else:

            raise HTTPException(status_code=403, detail="Acesso negado. Relato privado ou no publicado.")

    except Exception as e:

        logger.error(f"Pydantic validation error for relato {relato_id}: {e}")

        logger.error(f"Data passed to Pydantic: {mapped_data}")

        raise HTTPException(status_code=500, detail="Erro de validao de dados internos.")



async def list_pending_moderation_relatos(requesting_user: User) -> list:

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



async def listar_relatos_publicos_preview(limit: int = 50, status_filter: str = None) -> list:

    db = get_firestore_client()

    if not db:

        logger.error("Erro ao obter o cliente Firestore")

        raise HTTPException(status_code=500, detail="Erro interno no servidor.")



    try:

        docs = db.collection("relatos").limit(limit).stream()

        resultados = []

        for doc in docs:

            safe = normalize_public_preview(doc.to_dict(), doc.id, status_filter)

            if safe:

                resultados.append(safe)

        return resultados

    except Exception as e:

        logger.exception("Erro ao listar relatos pblicos para galeria.")

        raise HTTPException(status_code=500, detail=f"Erro ao acessar o Firestore: {str(e)}")




