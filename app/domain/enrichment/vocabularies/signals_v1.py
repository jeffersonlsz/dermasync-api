# app/domain/enrichment/vocabularies/signals_v1.py

"""
VocabulÃ¡rio controlado de sinais observÃ¡veis relatados pelo usuÃ¡rio.

Signals representam manifestaÃ§Ãµes percebidas diretamente,
nÃ£o inferÃªncias mÃ©dicas ou diagnÃ³sticas.

Regras:
- Baseado na percepÃ§Ã£o do usuÃ¡rio
- ComputÃ¡vel e estruturÃ¡vel
- Sem interpretaÃ§Ã£o clÃ­nica
"""

# -----------------------------
# Sinais observÃ¡veis
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
# FrequÃªncia percebida
# -----------------------------

ALLOWED_FREQUENCIES: set[str] = {
    "esporadica",
    "recorrente",
    "diaria",
}
