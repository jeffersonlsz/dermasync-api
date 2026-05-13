# app/domain/enrichment/vocabularies/signals_v1.py

"""
Vocabulrio controlado de sinais observveis relatados pelo usurio.

Signals representam manifestaes percebidas diretamente,
no inferncias mdicas ou diagnsticas.

Regras:
- Baseado na percepo do usurio
- Computvel e estruturvel
- Sem interpretao clnica
"""

# -----------------------------
# Sinais observveis
# -----------------------------

ALLOWED_SIGNALS: set[str] = {
    "prurido",
    "ardor",
    "dor",
    "ressecamento",
    "fissura",
    "sangramento",
    "secrecao",
    "espessamento",
    "hiperpigmentacao",
    "descamacao",
}

# -----------------------------
# Intensidade percebida
# -----------------------------

ALLOWED_INTENSITIES: set[str] = {
    "leve",
    "moderada",
    "alta",
}

# -----------------------------
# Frequncia percebida
# -----------------------------

ALLOWED_FREQUENCIES: set[str] = {
    "esporadica",
    "recorrente",
    "diaria",
}
