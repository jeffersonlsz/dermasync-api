# app/services/relato_normalizer.py

from typing import Dict, Any, List


def normalize_relato_document(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garante que o documento respeite o schema esperado pelo domÃ­nio.
    Corrige divergÃªncias legadas do Firestore.
    Retorna sempre uma estrutura canÃ´nica estÃ¡vel.
    """

    # ---------------------------------------------------------
    # CÃ³pia defensiva
    # ---------------------------------------------------------
    doc = dict(raw or {})

    # ---------------------------------------------------------
    # id â†’ sempre string
    # ---------------------------------------------------------
    if not isinstance(doc.get("id"), str):
        doc["id"] = str(doc.get("id") or "")

    # ---------------------------------------------------------
    # public_excerpt â†’ sempre objeto { text: str }
    # ---------------------------------------------------------
    public_excerpt = doc.get("public_excerpt")

    if isinstance(public_excerpt, str):
        doc["public_excerpt"] = {"text": public_excerpt}

    elif isinstance(public_excerpt, dict):
        text = public_excerpt.get("text")
        doc["public_excerpt"] = {
            "text": text if isinstance(text, str) else ""
        }

    else:
        doc["public_excerpt"] = {"text": ""}

    # ---------------------------------------------------------
    # tags_extraidas â†’ sempre lista[str]
    # ---------------------------------------------------------
    tags = doc.get("tags_extraidas")

    if isinstance(tags, list):
        doc["tags_extraidas"] = [
            str(tag) for tag in tags if isinstance(tag, (str, int, float))
        ]
    else:
        doc["tags_extraidas"] = []

    # ---------------------------------------------------------
    # conteudo_original â†’ sempre string
    # ---------------------------------------------------------
    if not isinstance(doc.get("conteudo_original"), str):
        doc["conteudo_original"] = ""

    # ---------------------------------------------------------
    # conteudo_anonimizado â†’ sempre string
    # ---------------------------------------------------------
    if not isinstance(doc.get("conteudo_anonimizado"), str):
        doc["conteudo_anonimizado"] = ""

    # ---------------------------------------------------------
    # image_refs â†’ sempre lista[{type: str, path: str}]
    # ---------------------------------------------------------
    images_raw = doc.get("image_refs")
    normalized_images: List[Dict[str, str]] = []

    if isinstance(images_raw, dict):
        # formato legado: { "antes": [path1, path2], "depois": [path3] }
        for img_type, paths in images_raw.items():
            if isinstance(img_type, str) and isinstance(paths, list):
                for path in paths:
                    if isinstance(path, str):
                        normalized_images.append({
                            "type": img_type,
                            "path": path
                        })

    elif isinstance(images_raw, list):
        # formato novo esperado: [{type, path}]
        for img in images_raw:
            if isinstance(img, dict):
                img_type = img.get("type")
                img_path = img.get("path")

                if isinstance(img_type, str) and isinstance(img_path, str):
                    normalized_images.append({
                        "type": img_type,
                        "path": img_path
                    })

    doc["image_refs"] = normalized_images
    return doc
