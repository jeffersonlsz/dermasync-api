# app/domain/enrichment/vocabularies/body_regions_v1.py

"""
Vocabulrio controlado de regies corporais.

Objetivo:
- Normalizar localizaes anatmicas citadas em relatos
- Permitir agregao, filtro e similaridade
- Evitar identificao pessoal ou granularidade excessiva

Regras:
- Sem lateralidade (direita/esquerda)
- Sem regies microanatmicas
- Vocabulrio fechado
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
    "nadegas",
    "gluteos",
    "ombro",
    "peito",
    "costas",
    "palma_da_mao",
    "planta_do_pe",
    
}
