# app/domain/enrichment/vocabularies/temporal_markers_v1.py

"""
Vocabulário controlado de marcadores temporais relativos.

Objetivo:
- Capturar noção de tempo sem datas absolutas
- Preservar anonimato
- Permitir análise longitudinal qualitativa

Regras:
- Apenas tempo relativo
- Sem datas
- Sem idades numéricas
"""

ALLOWED_TEMPORAL_MARKERS: set[str] = {
    "infancia",
    "adolescencia",
    "vida_adulta",
    "recente",
    "recorrente",
    "cronico",
}
