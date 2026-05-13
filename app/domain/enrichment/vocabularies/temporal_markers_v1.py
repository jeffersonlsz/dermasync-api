# app/domain/enrichment/vocabularies/temporal_markers_v1.py

"""
Vocabulrio controlado de marcadores temporais relativos.

Objetivo:
- Capturar noo de tempo sem datas absolutas
- Preservar anonimato
- Permitir anlise longitudinal qualitativa

Regras:
- Apenas tempo relativo
- Sem datas
- Sem idades numricas
"""

ALLOWED_TEMPORAL_MARKERS: set[str] = {
    "infancia",
    "adolescencia",
    "vida_adulta",
    "recente",
    "recorrente",
    "cronico",
}
