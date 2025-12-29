import logging
from typing import List, Optional
from fastapi import UploadFile

from app.services.imagens_service import salvar_imagem_bytes, salvar_imagem_uploadfile

logger = logging.getLogger(__name__)


def _filter_valid_uploads(files: Optional[List[UploadFile]]) -> List[UploadFile]:
    if not files:
        return []
    return [f for f in files if f and f.filename]


def noop_upload_images(*args, **kwargs):
    return None


def upload_relato_images(
    relato_id: str,
    imagens: dict,
):
    """
    Adapter técnico de upload de imagens.
    NÃO altera estado do relato.
    """

    for papel, arquivos in imagens.items():
        for arquivo in arquivos:
            try:
                salvar_imagem_uploadfile(
                    relato_id=relato_id,
                    file=arquivo,
                    papel_clinico=papel.upper(),
                )

                logger.info(
                    "[IMAGEM] Upload realizado | relato=%s papel=%s arquivo=%s",
                    relato_id,
                    papel,
                    arquivo.filename,
                )

            except Exception as exc:
                logger.error(
                    "[IMAGEM] Falha no upload | relato=%s papel=%s erro=%s",
                    relato_id,
                    papel,
                    exc,
                )


def upload_relato_images(
    relato_id: str,
    imagens: dict,
):
    """
    Adapter técnico de upload de imagens.
    Espera imagens já MATERIALIZADAS (bytes).
    NÃO altera estado do relato.
    """

    logger.debug(
        "[IMAGEM][ADAPTER] Iniciando processamento | relato=%s chaves=%s",
        relato_id,
        list(imagens.keys()),
    )

    for papel, arquivos in imagens.items():
        logger.debug(
            "[IMAGEM][ADAPTER] Papel=%s total_arquivos=%d",
            papel,
            len(arquivos),
        )

        for idx, arquivo in enumerate(arquivos):
            try:
                logger.debug(
                    "[IMAGEM][ADAPTER] Upload #%d | relato=%s papel=%s filename=%s size=%d",
                    idx + 1,
                    relato_id,
                    papel,
                    arquivo.get("filename"),
                    len(arquivo.get("content", b"")),
                )

                salvar_imagem_bytes(
                    relato_id=relato_id,
                    filename=arquivo["filename"],
                    content=arquivo["content"],
                    content_type=arquivo.get("content_type"),
                    papel_clinico=papel.upper(),
                )

            except Exception as exc:
                logger.error(
                    "[IMAGEM][ADAPTER] Falha no upload | relato=%s papel=%s erro=%s",
                    relato_id,
                    papel,
                    exc,
                    exc_info=True,
                )

