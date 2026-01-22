# app/domain/enrichment/vocabularies/signals_v1.py

"""
Vocabulário controlado de sinais observáveis relatados pelo usuário.

Signals representam manifestações percebidas diretamente,
não inferências médicas ou diagnósticas.

Regras:
- Baseado na percepção do usuário
- Computável e estruturável
- Sem interpretação clínica
"""

# -----------------------------
# Sinais observáveis
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
# Frequência percebida
# -----------------------------

ALLOWED_FREQUENCIES: set[str] = {
    "esporadica",
    "recorrente",
    "diaria",
}
