# app/services/imagens_service.py
"""
Serviços de Imagens — versão corrigida e otimizada
Compatível com Firebase Storage + Firestore
Sem uso incorreto de async-for
"""

import base64
import hashlib
import logging
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import List, Optional, Union

import magic
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.auth.schemas import User
from app.firestore.client import get_firestore_client, get_storage_bucket

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# CONSTANTES DE VALIDAÇÃO
# ---------------------------------------------------------
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE_MB = 10
MAX_DIMENSIONS = (4096, 4096)
# status públicos aceitos (expanda se precisar)
_PUBLIC_STATUSES = {"public", "approved_public", "approved", "published"}


# =========================================================
# 🔧 FUNÇÕES AUXILIARES
# =========================================================

def _to_iso_if_datetime(val) -> Optional[str]:
    """
    Se val for um datetime (ou tipo Firestore DatetimeWithNanoseconds),
    retorna string ISO 'YYYY-MM-DDTHH:MM:SS.sssZ'. Se for None, retorna None.
    """
    if val is None:
        return None
    try:
        # Firestore DatetimeWithNanoseconds pode ser convertido diretamente
        # se for subclass de datetime
        if isinstance(val, datetime):
            d = val
        elif hasattr(val, "to_datetime"):
            d = val.to_datetime()
        else:
            # não é datetime -> tentar parse string
            if isinstance(val, str):
                return val
            return str(val)
        # garantir timezone-aware UTC
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.isoformat().replace("+00:00", "Z")
    except Exception:
        try:
            return str(val)
        except Exception:
            return None


def _generate_signed_url_sync(storage_path: str, expires_seconds: int = 3600) -> Optional[str]:
    """Gera signed URL usando Firebase Storage (GCS) para um único storage_path."""
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_seconds),
            method="GET",
        )
        return url
    except Exception as e:
        logger.exception(f"Erro ao gerar signed URL para {storage_path}: {e}")
        return None


def _collect_sync(collection):
    """Executa stream síncrono de Firestore em thread."""
    docs = []
    for doc in collection.stream():
        d = doc.to_dict()
        d["id"] = doc.id
        docs.append(d)
    return docs


# compatibilidade: alias usado por versões anteriores
def _collect_public_images_sync(collection):
    """Alias simples para o coletor síncrono genérico."""
    return _collect_sync(collection)


def _generate_signed_urls_for_meta(image_meta: dict, expires_seconds: int = 3600) -> Optional[Union[str, dict]]:
    """
    Gera signed url(s) para image_meta.
    Retorna:
      - None se não houver paths/storage_path
      - string se 1 url
      - dict {'paths': [...], 'signed_urls': [...]} se >1
    Esta versão é resiliente a valores None e loga erros internamente.
    """
    try:
        if not isinstance(image_meta, dict):
            logger.warning("_generate_signed_urls_for_meta recebeu image_meta não-dict: %r", image_meta)
            return None

        paths = []
        if isinstance(image_meta.get("paths"), list) and image_meta.get("paths"):
            paths = [str(p).lstrip("/") for p in image_meta.get("paths")]
        elif image_meta.get("storage_path"):
            paths = [str(image_meta.get("storage_path")).lstrip("/")]
        else:
            return None

        signed_urls = []
        bucket = None
        for p in paths:
            url = None
            try:
                # tenta helper individual
                url = _generate_signed_url_sync(p, expires_seconds)
            except Exception as e:
                logger.debug("Helper _generate_signed_url_sync falhou para %s: %s", p, e)

            if not url:
                # fallback direto com bucket
                try:
                    if bucket is None:
                        bucket = get_storage_bucket()
                    blob = bucket.blob(p)
                    url = blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(seconds=expires_seconds),
                        method="GET",
                    )
                except Exception as e:
                    logger.exception("Falha ao gerar signed_url (fallback) para %s: %s", p, e)
                    url = None

            signed_urls.append(url)

        # normalize: se todas urls forem None -> retorna None
        if all(u is None for u in signed_urls):
            return None

        # se só 1 válida, retorne string (primeira não-nula)
        if len(signed_urls) == 1:
            return signed_urls[0]

        return {"paths": paths, "signed_urls": signed_urls}
    except Exception as e:
        logger.exception("Erro inesperado em _generate_signed_urls_for_meta: %s", e)
        return None


def _normalize_doc_for_response(im: dict) -> dict:
    """
    Garante shape e tipos (JSON-serializáveis) para a resposta.
    - converte datetimes para ISO strings
    - preenche campos obrigatórios com defaults seguros
    - mantém campo 'raw' com o doc original para depuração
    """
    if not isinstance(im, dict):
        im = {}

    owner_user_id = im.get("owner_user_id") or im.get("owner") or ""
    original_filename = im.get("original_filename") or im.get("filename") or ""
    content_type = im.get("content_type") or im.get("mime_type") or ""
    sha256 = im.get("sha256") or ""
    # ints seguros
    try:
        size_bytes = int(im.get("size_bytes")) if im.get("size_bytes") is not None else 0
    except Exception:
        size_bytes = 0
    try:
        width = int(im.get("width")) if im.get("width") is not None else 0
    except Exception:
        width = 0
    try:
        height = int(im.get("height")) if im.get("height") is not None else 0
    except Exception:
        height = 0

    created_at_raw = im.get("created_at") or im.get("criado_em") or im.get("createdAt") or None
    updated_at_raw = im.get("updated_at") or im.get("updated_em") or im.get("updatedAt") or None

    created_at = _to_iso_if_datetime(created_at_raw) or _to_iso_if_datetime(updated_at_raw) or _to_iso_if_datetime(datetime.now(timezone.utc))
    updated_at = _to_iso_if_datetime(updated_at_raw) or created_at

    # storage_path: prioriza campo storage_path; caso não exista, usa primeiro path de 'paths' (se houver)
    storage_path = im.get("storage_path")
    if not storage_path:
        paths = im.get("paths")
        if isinstance(paths, list) and len(paths) > 0:
            storage_path = paths[0]
        else:
            storage_path = ""

    norm = {
        "id": im.get("id") or im.get("_id") or "",
        "owner_user_id": str(owner_user_id),
        "original_filename": str(original_filename),
        "content_type": str(content_type),
        "size_bytes": int(size_bytes),
        "width": int(width),
        "height": int(height),
        "sha256": str(sha256),
        "storage_path": str(storage_path),
        "created_at": created_at,
        "updated_at": updated_at,
        "status": im.get("status"),
        "paths": im.get("paths") if isinstance(im.get("paths"), list) else None,
        "title": im.get("title") or im.get("titulo") or None,
        "description": im.get("description") or im.get("descricao") or None,
        "raw": im,
    }

    return norm


# =========================================================
# 📤 UPLOAD
# =========================================================

async def _process_and_save_image_content(content: bytes, owner_user_id: str, original_filename: str) -> dict:
    # --------------------
    # 1. Validação
    # --------------------
    file_size_bytes = len(content)
    if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Arquivo muito grande. Máx: {MAX_FILE_SIZE_MB}MB.")

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Tipo não suportado: {mime_type}")

    try:
        with Image.open(BytesIO(content)) as img:
            width, height = img.size
            if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                raise HTTPException(413, f"Dimensões máximas excedidas: {width}x{height}px")
    except Exception:
        raise HTTPException(422, "Arquivo de imagem inválido")

    # --------------------
    # 2. Upload
    # --------------------
    image_uuid = uuid.uuid4().hex
    ext = mime_type.split("/")[-1]
    storage_path = f"raw/{owner_user_id}/{image_uuid}.{ext}"

    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)
        blob.upload_from_string(content, content_type=mime_type)
    except Exception as e:
        logger.exception("Falha ao enviar imagem para Storage.")
        raise HTTPException(500, str(e))

    # --------------------
    # 3. Metadados Firestore
    # --------------------
    db = get_firestore_client()
    image_id = uuid.uuid4().hex  # ID do documento

    # Usar strings ISO para evitar DatetimeWithNanoseconds em retorno direto
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata = {
        "id": image_id,
        "owner_user_id": owner_user_id,
        "status": "public",  # padrão: public para aparecer na galeria (ajuste conforme sua política)
        "original_filename": original_filename,
        "content_type": mime_type,
        "size_bytes": file_size_bytes,
        "width": width,
        "height": height,
        "storage_path": storage_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    await asyncio.to_thread(db.collection("imagens").document(image_id).set, metadata)

    logger.info("Imagem salva: %s (storage_path=%s)", image_id, storage_path)
    return metadata


async def salvar_imagem(file: UploadFile, owner_user_id: str) -> dict:
    content = await file.read()
    return await _process_and_save_image_content(
        content=content,
        owner_user_id=owner_user_id,
        original_filename=file.filename,
    )


# compatibilidade: recria salvar_imagem_from_base64 que outros módulos importam
async def salvar_imagem_from_base64(base64_str: str, owner_user_id: str, filename: str) -> dict:
    """
    Decodifica base64 e delega ao pipeline de processamento/salvamento.
    Mantido para compatibilidade com outros serviços (ex.: relatos_service).
    """
    try:
        content = base64.b64decode(base64_str)
    except Exception as e:
        logger.exception("Falha ao decodificar base64: %s", e)
        raise HTTPException(status_code=422, detail="String base64 inválida.")

    return await _process_and_save_image_content(
        content=content,
        owner_user_id=owner_user_id,
        original_filename=filename,
    )


# =========================================================
# 🔍 LISTAGEM PÚBLICA
# =========================================================

def _iso_to_datetime(s: str) -> Optional[datetime]:
    """Converte uma string ISO (com ou sem 'Z') para datetime UTC; retorna None se falhar."""
    if not s or not isinstance(s, str):
        return None
    try:
        # Trata 'Z' (Zulu) como +00:00
        if s.endswith("Z"):
            s2 = s.replace("Z", "+00:00")
        else:
            s2 = s
        return datetime.fromisoformat(s2)
    except Exception:
        try:
            # fallback: tentar parse parcial
            return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            return None


async def listar_imagens_publicas(include_signed_url: bool = False) -> List[dict]:
    """
    Lista metadados de imagens públicas normalizando shape e types esperados pelo response_model.
    Preenche campos obrigatórios com defaults válidos ('' para strings, 0 para ints, datetime ISO para datas).
    """
    db = get_firestore_client()
    coll = db.collection("imagens")

    # coleta todos os documentos de forma síncrona dentro de thread
    try:
        raw_docs = await asyncio.to_thread(_collect_sync, coll)
    except Exception as e:
        logger.exception("Falha ao coletar docs de imagens: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao acessar Firestore.")

    # filtra por status público aceito (case-insensitive)
    imagens_publicas_raw = [im for im in raw_docs if (im.get("status") or "").lower() in _PUBLIC_STATUSES]

    normalized = []
    for im in imagens_publicas_raw:
        norm = _normalize_doc_for_response(im)
        normalized.append(norm)

    # signed urls (defensivo). Gera signed_url(s) com base em storage_path ou em paths[]
    if include_signed_url and normalized:
        def _attach_signed_sync(imgs):
            for item in imgs:
                signed_urls = []
                try:
                    sp = item.get("storage_path")
                    if sp:
                        s = _generate_signed_url_sync(sp)
                        if s:
                            signed_urls.append(s)
                    # se não gerou ou houver paths, tenta gerar para cada path (compatibilidade)
                    if not signed_urls and item.get("paths"):
                        for p in item.get("paths") or []:
                            try:
                                s2 = _generate_signed_url_sync(p)
                                if s2:
                                    signed_urls.append(s2)
                            except Exception:
                                logger.debug("Falha ao gerar signed_url para path %s (ignorado)", p)
                except Exception as ex:
                    logger.exception("Erro ao gerar signed URLs para %s: %s", item.get("id"), ex)

                # anexa resultados (pode ser lista vazia)
                item["signed_urls"] = signed_urls if signed_urls else None
                item["signed_url"] = signed_urls[0] if signed_urls else None
            return imgs

        normalized = await asyncio.to_thread(_attach_signed_sync, normalized)

    return normalized


# =========================================================
# 🔍 GET PÚBLICO POR ID
# =========================================================

async def get_public_imagem_by_id(image_id: str, include_signed_url: bool = False) -> dict:
    """
    Retorna dados de uma imagem pública pelo ID.
    Aceita qualquer status dentro de _PUBLIC_STATUSES.
    """
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)

    doc = await asyncio.to_thread(doc_ref.get)

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    imagem_data = doc.to_dict() or {}
    imagem_data["id"] = image_id

    status = (imagem_data.get("status") or "").lower()
    if status not in _PUBLIC_STATUSES:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    # normalizar / serializar
    norm = _normalize_doc_for_response(imagem_data)

    if include_signed_url:
        try:
            signed = _generate_signed_urls_for_meta(imagem_data)
            if signed:
                norm["signed_url"] = signed
        except Exception as e:
            logger.exception(f"Erro ao gerar signed_url para imagem {image_id}: {e}")

    return norm


# =========================================================
# 🔐 LISTAGEM ADMIN
# =========================================================

async def listar_todas_imagens_admin(requesting_user: User) -> List[dict]:
    if requesting_user.role not in ["admin", "colaborador"]:
        raise HTTPException(403, "Acesso negado.")

    db = get_firestore_client()

    try:
        raw_docs = await asyncio.to_thread(lambda: [doc.to_dict() | {"id": doc.id} for doc in db.collection("imagens").stream()])
    except Exception as e:
        logger.exception("Erro ao coletar imagens para admin: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao acessar Firestore.")

    # normaliza todos para retorno seguro
    return [ _normalize_doc_for_response(d) for d in raw_docs ]


# =========================================================
# 🔑 GET PRIVADO + SIGNED URL
# =========================================================

async def get_imagem_by_id(image_id: str, requesting_user: User) -> dict:
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)

    doc = await asyncio.to_thread(doc_ref.get)

    if not doc.exists:
        raise HTTPException(404, "Imagem não encontrada.")

    data = doc.to_dict() or {}

    if requesting_user.role not in ["admin", "colaborador"] and data.get("owner_user_id") != requesting_user.id:
        raise HTTPException(403, "Acesso negado.")

    # normaliza e retorna (evita DatetimeWithNanoseconds)
    return _normalize_doc_for_response(data)


async def get_imagem_signed_url(image_id: str, requesting_user: User, expires_seconds: int = 300) -> Union[str, dict]:
    """
    Gera signed URL(s) para uma imagem (privada/admin). Retorna string ou dict.
    """
    try:
        data = await get_imagem_by_id(image_id, requesting_user)

        # data já normalizado mas _generate_signed_urls_for_meta aceita dicts contendo 'storage_path'/'paths'
        signed = _generate_signed_urls_for_meta(data, expires_seconds)
        if not signed:
            raise HTTPException(status_code=500, detail="storage_path ou paths ausente nos metadados da imagem.")

        return signed
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro em get_imagem_signed_url: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar signed URL: {str(e)}")


# =========================================================
# ⚠️ MARCAR COMO ORPHAN
# =========================================================

async def mark_image_as_orphaned(image_id: str):
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)
    await asyncio.to_thread(
        doc_ref.update, {"status": "orphaned", "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    )
    logger.info(f"Imagem {image_id} marcada como orphaned.")
