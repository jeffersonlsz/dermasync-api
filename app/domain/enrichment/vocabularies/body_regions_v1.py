# app/domain/enrichment/vocabularies/body_regions_v1.py

"""
VocabulÃ¡rio controlado de regiÃµes corporais.

Objetivo:
- Normalizar localizaÃ§Ãµes anatÃ´micas citadas em relatos
- Permitir agregaÃ§Ã£o, filtro e similaridade
- Evitar identificaÃ§Ã£o pessoal ou granularidade excessiva

Regras:
- Sem lateralidade (direita/esquerda)
- Sem regiÃµes microanatÃ´micas
- VocabulÃ¡rio fechado
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
