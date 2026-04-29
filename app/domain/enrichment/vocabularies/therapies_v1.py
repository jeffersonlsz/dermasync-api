# app/domain/enrichment/vocabularies/therapies_v1.py

"""
VocabulÃ¡rio controlado de terapias relatadas pelo usuÃ¡rio.

Este mÃ³dulo define APENAS categorias computÃ¡veis de intervenÃ§Ãµes mencionadas
em relatos humanos. NÃ£o representa prescriÃ§Ã£o mÃ©dica, recomendaÃ§Ã£o clÃ­nica
ou eficÃ¡cia terapÃªutica real.

Regras:
- VocabulÃ¡rio fechado (adiÃ§Ãµes exigem versionamento)
- Sem marcas comerciais
- Sem dosagens
- Sem inferÃªncia clÃ­nica
- Baseado em percepÃ§Ã£o do usuÃ¡rio
"""

# -----------------------------
# Tipos de intervenÃ§Ã£o
# -----------------------------

ALLOWED_THERAPY_TYPES: set[str] = {
    # AplicaÃ§Ãµes na pele
    "topico",

    # Medicamentos ingeridos
    "oral",

    # Rotina de higiene / cuidados com a pele
    "higienico",

    # MudanÃ§as de hÃ¡bito ou comportamento
    "comportamental",

    # Quando o relato menciona algo fora do escopo inicial
    "outro",
}

# -----------------------------
# SubstÃ¢ncias / categorias amplas
# -----------------------------

ALLOWED_SUBSTANCES: set[str] = {
    # Classes farmacolÃ³gicas amplas
    "corticoide",
    "antihistaminico",
    "antibiotico",
    "imunossupressor",

    # Cuidados com a pele
    "hidratante",
    "sabao_neutro",

    # Alternativos / nÃ£o farmacolÃ³gicos
    "fitoterapico",
    "oleo_natural",

    # Quando nÃ£o Ã© possÃ­vel classificar
    "outro",
}

# -----------------------------
# Resposta percebida pelo usuÃ¡rio
# -----------------------------

ALLOWED_RESPONSES: set[str] = {
    # PercepÃ§Ã£o clara de melhora
    "melhora",

    # Algum alÃ­vio, mas sintomas persistem
    "melhora_parcial",

    # Nenhuma mudanÃ§a percebida
    "sem_resposta",

    # Piora percebida apÃ³s uso
    "piora",

    # Relato menciona uso, mas nÃ£o descreve resultado
    "desconhecida",
}
