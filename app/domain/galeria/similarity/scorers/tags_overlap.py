# app/domain/galeria/similarity/scorers/tags_overlap.py

from typing import List, Set


def _normalize(tags: List[str]) -> Set[str]:
    return {
        tag.strip().lower()
        for tag in tags
        if isinstance(tag, str)
    }


def jaccard_similarity(
    tags_a: List[str],
    tags_b: List[str],
) -> float:
    """
    Similaridade auditÃ¡vel com penalizaÃ§Ã£o por baixa cardinalidade.
    Evita que 1 tag gere score 1.0 absoluto.
    """

    set_a = _normalize(tags_a)
    set_b = _normalize(tags_b)

    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b
    union = set_a | set_b

    base_similarity = len(intersection) / len(union)

    # PenalizaÃ§Ã£o por baixa informaÃ§Ã£o
    # mÃ­nimo de 3 tags para confianÃ§a total
    min_cardinality = min(len(set_a), len(set_b))
    confidence = min(min_cardinality / 3.0, 1.0)

    return round(base_similarity * confidence, 4)
