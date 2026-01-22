# app/domain/enrichment/vocabularies/body_regions_v1.py

"""
Vocabulário controlado de regiões corporais.

Objetivo:
- Normalizar localizações anatômicas citadas em relatos
- Permitir agregação, filtro e similaridade
- Evitar identificação pessoal ou granularidade excessiva

Regras:
- Sem lateralidade (direita/esquerda)
- Sem regiões microanatômicas
- Vocabulário fechado
"""

ALLOWED_BODY_REGIONS: set[str] = {
    "rosto",
    "face",
    "couro_cabeludo",
    "pescoco",
    "axila",
    "dobra_cotovelo",
    "antebraco",
    "mao",
    "tronco",
    "abdomen",
    "virilha",
    "coxa",
    "joelho",
    "perna",
    "pe",
}
