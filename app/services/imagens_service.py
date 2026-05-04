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
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import List, Optional, Union, Dict, Any

import magic
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.auth.schemas import User
from app.firestore.client import get_firestore_client, get_storage_bucket
from google.cloud.firestore import FieldFilter

logger = logging.getLogger(__name__)


from google.cloud import storage



BUCKET_NAME = "dermasync-3d14a.firebasestorage.app"  # ⚠️ ajuste se necessario

# ---------------------------------------------------------
# CONSTANTES DE VALIDAÇÃO
# ---------------------------------------------------------
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE_MB = 10
MAX_DIMENSIONS = (4096, 4096)
# status pablicos aceitos (expanda se precisar)
_PUBLIC_STATUSES = {"public", "approved_public", "approved", "published"}


# =========================================================
# 🔧 FUNÇÕES AUXILIARES
# =========================================================

def normalize_storage_path(path: str) -> str:
    """
    Normaliza um path do Firebase Storage, garantindo que seja apenas o caminho interno.
    Aceita paths completos (https://...) ou já internos.
    """
    if not path:
        return ""
    
    path = str(path).strip()
    
    # Se for uma URL HTTP, precisamos extrair apenas a rota (o caminho interno do objeto)
    if path.startswith("http://") or path.startswith("https://"):
        parsed = urllib.parse.urlparse(path)
        path = parsed.path
        
    # Remove prefixos indesejados da API do GCP/Firebase
    # O path do GCP pode ser /v0/b/{bucket}/o/{path}
    if "/v0/b/" in path:
        parts = path.split("/o/")
        if len(parts) > 1:
            path = urllib.parse.unquote(parts[1])
            # Remove query params
            path = path.split("?")[0]
            
    # Removendo bucket prefix se houver (caso a rota seja /{bucket_name}/...)
    bucket_name = BUCKET_NAME
    if f"/{bucket_name}/" in path:
        path = path.split(f"/{bucket_name}/")[-1]
    elif path.startswith(f"{bucket_name}/"):
        path = path[len(bucket_name)+1:]

    # Remove barras iniciais
    return path.lstrip("/")


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
    """Gera signed URL usando Firebase Storage (GCS) para um anico storage_path."""
    if not storage_path:
        return None

    try:
        normalized_path = normalize_storage_path(storage_path)
        if not normalized_path:
            return None

        bucket = get_storage_bucket()
        blob = bucket.blob(normalized_path)
        
        emulator_host = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")
        if emulator_host:
            encoded_path = urllib.parse.quote(normalized_path, safe="")
            url = f"http://{emulator_host}/v0/b/{bucket.name}/o/{encoded_path}?alt=media"
            logger.info(f"Gerando URL do emulador para {normalized_path}")
            return url

        logger.info(f"Gerando signed URL para {normalized_path} (original: {storage_path}) com expiraaao de {expires_seconds} segundos.")
        
        if not blob.exists():
            logger.warning(f"Blob não existe no bucket {bucket.name}: {normalized_path}")
            return None
            
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


# compatibilidade: alias usado por versaes anteriores
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
    Esta versão resiliente a valores None e loga erros internamente.
    """
    try:
        if not isinstance(image_meta, dict):
            logger.warning("_generate_signed_urls_for_meta recebeu image_meta no-dict: %r", image_meta)
            return None

        paths = []
        if isinstance(image_meta.get("paths"), list) and image_meta.get("paths"):
            paths = [str(p).lstrip("/") for p in image_meta.get("paths")]
        elif image_meta.get("storage_path"):
            paths = [str(image_meta.get("storage_path")).lstrip("/")]
        else:
            return None

        signed_urls = []
        for p in paths:
            url = None
            try:
                # O helper _generate_signed_url_sync ja lida com emulator, existance check e fallback interno.
                url = _generate_signed_url_sync(p, expires_seconds)
            except Exception as e:
                logger.debug("Helper _generate_signed_url_sync falhou para %s: %s", p, e)

            signed_urls.append(url)

        # normalize: se todas urls forem None -> retorna None
        if all(u is None for u in signed_urls):
            return None

        # se sa 1 valida, retorne string (primeira nao-nula)
        if len(signed_urls) == 1:
            return signed_urls[0]

        return {"paths": paths, "signed_urls": signed_urls}
    except Exception as e:
        logger.exception("Erro inesperado em _generate_signed_urls_for_meta: %s", e)
        return None


def _normalize_doc_for_response(im: dict) -> dict:
    """
    Garante shape e tipos (JSON-serializaveis) para a resposta.
    - converte datetimes para ISO strings
    - preenche campos obrigatarios com defaults seguros
    - mantam campo 'raw' com o doc original para depuraaao
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

    # storage_path: prioriza campo storage_path; caso nao exista, usa primeiro path de 'paths' (se houver)
    storage_path = im.get("storage_path")
    if not storage_path:
        paths = im.get("paths")
        if isinstance(paths, list) and len(paths) > 0:
            storage_path = paths[0]
        else:
            storage_path = ""

    storage_path = normalize_storage_path(storage_path) if storage_path else ""

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
    # 1. Validaaao
    # --------------------
    file_size_bytes = len(content)
    if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Arquivo muito grande. Max: {MAX_FILE_SIZE_MB}MB.")

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Tipo nao suportado: {mime_type}")

    try:
        with Image.open(BytesIO(content)) as img:
            width, height = img.size
            if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                raise HTTPException(413, f"Dimensaes maximas excedidas: {width}x{height}px")
    except Exception:
        raise HTTPException(422, "Arquivo de imagem invalido")

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
        "status": "public",  # padrao: public para aparecer na galeria (ajuste conforme sua polatica)
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


# compatibilidade: recria salvar_imagem_from_base64 que outros madulos importam
async def salvar_imagem_from_base64(base64_str: str, owner_user_id: str, filename: str) -> dict:
    """
    Decodifica base64 e delega ao pipeline de processamento/salvamento.
    Mantido para compatibilidade com outros serviaos (ex.: relatos_service).
    """
    try:
        content = base64.b64decode(base64_str)
    except Exception as e:
        logger.exception("Falha ao decodificar base64: %s", e)
        raise HTTPException(status_code=422, detail="String base64 invalida.")

    return await _process_and_save_image_content(
        content=content,
        owner_user_id=owner_user_id,
        original_filename=filename,
    )


def salvar_imagem_bytes_to_storage(storage_path: str, content: bytes, content_type: str) -> Optional[str]:
    """
    Salva bytes de uma imagem em um caminho especafico no Firebase Storage.
    Retorna uma signed URL para o objeto.
    Esta a uma funaao sancrona, projetada para ser usada em background tasks.
    """
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)
        blob.upload_from_string(content, content_type=content_type)
        
        # Gera e retorna uma signed URL para acesso
        signed_url = _generate_signed_url_sync(storage_path)
        logger.info(f"Imagem salva em {storage_path}. URL assinada gerada.")
        return signed_url
    except Exception as e:
        logger.exception(f"Falha ao enviar imagem para Storage em {storage_path}.")
        # Lanaar exceaao para que a background task possa capturar e logar o erro.
        raise






def salvar_imagem_bytes(
    *,
    relato_id: str,
    filename: str,
    content: bytes,
    content_type: str | None,
    papel_clinico: str,
) -> dict:
    """
    Persiste imagem no Firebase Storage / GCS a partir de bytes.
    Retorna metadados basicos do upload.
    """
    logger.debug("[IMAGEM][UPLOAD] Salvando imagem bytes | relato=%s papel=%s filename=%s size=%d",
                 relato_id, papel_clinico, filename, len(content))
    if not content:
        raise ValueError("Conteado da imagem vazio")

    bucket = get_storage_bucket()

    ext = filename.split(".")[-1] if "." in filename else "bin"
    image_id = uuid.uuid4().hex

    object_path = (
        f"relatos/{relato_id}/"
        f"{papel_clinico.lower()}/"
        f"{image_id}.{ext}"
    )

    blob = bucket.blob(object_path)

    logger.debug(
        "[IMAGEM][UPLOAD] Iniciando upload | relato=%s papel=%s path=%s size=%d",
        relato_id,
        papel_clinico,
        object_path,
        len(content),
    )

    blob.upload_from_string(
        content,
        content_type=content_type or "application/octet-stream",
    )

    blob.metadata = {
        "relato_id": relato_id,
        "papel_clinico": papel_clinico,
        "original_filename": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    blob.patch()

    logger.info(
        "[IMAGEM][UPLOAD] Upload concluado | relato=%s papel=%s path=%s",
        relato_id,
        papel_clinico,
        object_path,
    )

    return {
        "storage_path": object_path,
        "content_type": content_type,
        "size": len(content),
    }



def salvar_imagem_uploadfile(
    *,
    relato_id: str,
    file: UploadFile,
    papel_clinico: str,
) -> dict:
    """
    Salva uma imagem enviada via UploadFile no Storage.

    Responsabilidade:
    - Persistancia tacnica
    - Organizaaao por relato e papel clanico
    - NÃO altera estado de domanio
    """

    if not file.filename:
        raise ValueError("Arquivo sem nome")

    bucket = get_storage_bucket()

    extensao = file.filename.split(".")[-1].lower()
    imagem_id = uuid.uuid4().hex

    # =========================
    # Path cananico
    # =========================
    storage_path = (
        f"relatos/{relato_id}/imagens/"
        f"{papel_clinico.lower()}/{imagem_id}.{extensao}"
    )

    blob = bucket.blob(storage_path)

    try:
        blob.upload_from_file(
            file.file,
            content_type=file.content_type,
        )

        blob.metadata = {
            "relato_id": relato_id,
            "papel_clinico": papel_clinico,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "original_filename": file.filename,
        }
        blob.patch()

        logger.info(
            "[STORAGE] Imagem salva | relato=%s papel=%s path=%s",
            relato_id,
            papel_clinico,
            storage_path,
        )

        return {
            "storage_path": storage_path,
            "papel_clinico": papel_clinico,
            "filename": file.filename,
        }

    except Exception as exc:
        logger.exception(
            "[STORAGE] Erro ao salvar imagem | relato=%s papel=%s",
            relato_id,
            papel_clinico,
        )
        raise exc



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


async def listar_imagens_publicas(include_signed_url: bool = False, thumb: bool = False) -> List[dict]:
    """
    Lista metadados de imagens pablicas normalizando shape e types esperados pelo response_model.
    Preenche campos obrigatarios com defaults validos ('' para strings, 0 para ints, datetime ISO para datas).

    Parametros:
      - include_signed_url: se True, anexa campos signed (signed_url, signed_urls).
      - thumb: se True, tenta localizar um thumbnail e anexa thumb_url (signed). Se nao existir thumb, usa image_url como fallback.
    """
    db = get_firestore_client()
    coll = db.collection("imagens")

    # coleta todos os documentos de forma sancrona dentro de thread
    try:
        raw_docs = await asyncio.to_thread(_collect_sync, coll)
    except Exception as e:
        logger.exception("Falha ao coletar docs de imagens: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao acessar Firestore.")

    # filtra por status pablico aceito (case-insensitive)
    imagens_publicas_raw = [im for im in raw_docs if (im.get("status") or "").lower() in _PUBLIC_STATUSES]

    normalized = []
    for im in imagens_publicas_raw:
        norm = _normalize_doc_for_response(im)
        normalized.append(norm)

    # signed urls (defensivo). Gera signed_url(s) com base em storage_path ou em paths[]
    if include_signed_url and normalized:
        def _attach_signed_sync(imgs, thumb_flag: bool):
            """
            Funaao sancrona que anexa signed URLs a cada item. Sera executada em thread via asyncio.to_thread.
            """
            for item in imgs:
                signed_urls = []
                image_url = None
                thumb_url = None
                try:
                    sp = item.get("storage_path")
                    # 1) full image a partir de storage_path
                    if sp:
                        s = _generate_signed_url_sync(sp)
                        if s:
                            signed_urls.append(s)
                            image_url = image_url or s

                    # 2) se nao gerou via storage_path, tenta paths[]
                    if not signed_urls and item.get("paths"):
                        for p in item.get("paths") or []:
                            try:
                                s2 = _generate_signed_url_sync(p)
                                if s2:
                                    signed_urls.append(s2)
                                    image_url = image_url or s2
                            except Exception:
                                logger.debug("Falha ao gerar signed_url para path %s (ignorado)", p)

                    # 3) se thumb solicitado, tente heurasticas de thumb
                    if thumb_flag:
                        # candidates baseados em id + original filename
                        candidates = []
                        orig = (item.get("original_filename") or "").strip()
                        id_part = item.get("id") or ""
                        if orig:
                            # thumb with prefix
                            candidates.append(f"{id_part}/thumb_{orig}")
                            # thumb with same filename under a thumb/ or thumbnail/
                            candidates.append(f"{id_part}/thumb_{orig.split('/')[-1]}")
                        # generic candidates
                        candidates.append(f"{id_part}/thumb.jpg")
                        candidates.append(f"{id_part}/thumbnail.jpg")
                        candidates.append(f"{id_part}/thumb_{id_part}.jpg")
                        # tentar cada candidate ata encontrar um existente (por tentativa de signed_url)
                        for cand in candidates:
                            try:
                                s_thumb = _generate_signed_url_sync(cand)
                                if s_thumb:
                                    thumb_url = s_thumb
                                    break
                            except Exception:
                                logger.debug("Falha ao gerar signed_url para candidate thumb %s (ignorado)", cand)
                        # fallback heurastico: tentar gerar signed_url para "<id>/antes_<orig>" e "<id>/depois_<orig>" (caso padrao do upload)
                        if not thumb_url and orig:
                            try:
                                alt1 = f"{id_part}/antes_{orig}"
                                s_alt1 = _generate_signed_url_sync(alt1)
                                if s_alt1:
                                    thumb_url = s_alt1
                            except Exception:
                                pass
                            if not thumb_url:
                                try:
                                    alt2 = f"{id_part}/depois_{orig}"
                                    s_alt2 = _generate_signed_url_sync(alt2)
                                    if s_alt2:
                                        thumb_url = s_alt2
                                except Exception:
                                    pass

                    # 4) fallback: se nenhuma thumb encontrada e existe image_url, usar a image_url como thumb
                    if not thumb_url and image_url:
                        thumb_url = image_url

                except Exception as ex:
                    logger.exception("Erro ao gerar signed URLs para %s: %s", item.get("id"), ex)

                # anexa resultados (pode ser lista vazia/None)
                item["signed_urls"] = signed_urls if signed_urls else None
                item["signed_url"] = signed_urls[0] if signed_urls else None
                item["image_url"] = image_url
                item["thumb_url"] = thumb_url
            return imgs

        # Executa a versao sancrona em thread
        try:
            normalized = await asyncio.to_thread(_attach_signed_sync, normalized, thumb)
        except TypeError as te:
            # Caso o caller nao espere thumb param no service original, tentamos sem thumb (fallback defensivo)
            logger.warning("listar_imagens_publicas _attach_signed_sync TypeError: %s. Retry without thumb", te)
            normalized = await asyncio.to_thread(_attach_signed_sync, normalized, False)
        except Exception as e:
            logger.exception("Erro ao anexar signed urls (thread): %s", e)
            # nao falhar totalmente: retornar normalized sem signed urls
            # mas logar para correaao
            return normalized

    return normalized


# =========================================================
# 🔍 GET PÚBLICO POR ID
# =========================================================

async def get_public_imagem_by_id(image_id: str, include_signed_url: bool = False) -> dict:
    """
    Retorna dados de uma imagem pablica pelo ID.
    Aceita qualquer status dentro de _PUBLIC_STATUSES.
    """
    db = get_firestore_client()
    doc_ref = db.collection("imagens").document(image_id)

    doc = await asyncio.to_thread(doc_ref.get)

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Imagem nao encontrada.")

    imagem_data = doc.to_dict() or {}
    imagem_data["id"] = image_id

    status = (imagem_data.get("status") or "").lower()
    if status not in _PUBLIC_STATUSES:
        raise HTTPException(status_code=404, detail="Imagem nao encontrada.")

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
        raise HTTPException(404, "Imagem nao encontrada.")

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

        # data ja normalizado mas _generate_signed_urls_for_meta aceita dicts contendo 'storage_path'/'paths'
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

# =========================================================
# 🧠 IMAGENS POR RELATO (CANÔNICO PARA FRONT)
# =========================================================




def _is_public_and_approved(img: dict) -> bool:
    status = img.get("status") or {}
    return (
        status.get("visibilidade") == "public"
        and status.get("moderacao") == "approved"
    )


def _image_to_front_dto(img: dict) -> dict:
    storage = img.get("storage") or {}

    thumb_path = storage.get("thumb_path")
    original_path = storage.get("original_path")

    thumb_url = _generate_signed_url_sync(thumb_path) if thumb_path else None
    full_url = _generate_signed_url_sync(original_path) if original_path else None

    return {
        "thumb_url": thumb_url,
        "full_url": full_url,
        "ordem": img.get("ordem"),
        "width": img.get("width"),
        "height": img.get("height"),
    }


async def get_imagens_por_relato(
    relato_id: str,
    include_private: bool = False
) -> Dict[str, Any]:
    """
    Resolve imagens associadas a um relato, ja filtradas, ordenadas
    e com signed URLs prontas para o front.
    """

    db = get_firestore_client()

    query = db.collection("imagens").where(
        filter=FieldFilter("relato_id", "==", relato_id)
    )

    raw_docs = await asyncio.to_thread(
        lambda: [doc.to_dict() for doc in query.stream()]
    )

    antes = None
    depois = None
    durante = []

    for img in raw_docs:
        if not include_private and not _is_public_and_approved(img):
            continue

        papel = img.get("papel_clinico")

        if papel == "ANTES":
            antes = _image_to_front_dto(img)

        elif papel == "DEPOIS":
            depois = _image_to_front_dto(img)

        elif papel == "DURANTE":
            durante.append(_image_to_front_dto(img))

    # ordenar DURANTE
    durante.sort(key=lambda x: x.get("ordem") or 0)

    return {
        "antes": antes,
        "durante": durante,
        "depois": depois,
    }
