# app/domain/galeria/similarity/scorers/narrative_tone.py

def narrative_tone_similarity(
    text_a: str,
    text_b: str,
) -> float:
    """
    Heurstica v1:
    - tamanho parecido
    - presena de palavras de progresso
    """
    if not text_a or not text_b:
        return 0.0

    len_ratio = min(len(text_a), len(text_b)) / max(len(text_a), len(text_b))

    positive_markers = [
        "melhora",
        "controle",
        "evoluo",
        "resultado",
        "alvio",
    ]

    def score_markers(text: str) -> int:
        text = text.lower()
        return sum(1 for m in positive_markers if m in text)

    markers_a = score_markers(text_a)
    markers_b = score_markers(text_b)

    marker_score = 1.0 if markers_a == markers_b else 0.5

    return round(0.6 * len_ratio + 0.4 * marker_score, 4)
