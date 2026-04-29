# app/domain/enrichment/vocabularies/temporal_markers_v1.py

"""
VocabulÃ¡rio controlado de marcadores temporais relativos.

Objetivo:
- Capturar noÃ§Ã£o de tempo sem datas absolutas
- Preservar anonimato
- Permitir anÃ¡lise longitudinal qualitativa

Regras:
- Apenas tempo relativo
- Sem datas
- Sem idades numÃ©ricas
"""

ALLOWED_TEMPORAL_MARKERS: set[str] = {
    "infancia",
    "adolescencia",
    "vida_adulta",
    "recente",
    "recorrente",
    "cronico",
}
