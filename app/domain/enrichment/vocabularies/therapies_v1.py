# app/domain/enrichment/vocabularies/therapies_v1.py

"""
Vocabulrio controlado de terapias relatadas pelo usurio.

Este mdulo define APENAS categorias computveis de intervenes mencionadas
em relatos humanos. No representa prescrio mdica, recomendao clnica
ou eficcia teraputica real.

Regras:
- Vocabulrio fechado (adies exigem versionamento)
- Sem marcas comerciais
- Sem dosagens
- Sem inferncia clnica
- Baseado em percepo do usurio
"""

# -----------------------------
# Tipos de interveno
# -----------------------------

ALLOWED_THERAPY_TYPES: set[str] = {
    # Aplicaes na pele
    "topico",

    # Medicamentos ingeridos
    "oral",

    # Rotina de higiene / cuidados com a pele
    "higienico",

    # Mudanas de hbito ou comportamento
    "comportamental",

    # Quando o relato menciona algo fora do escopo inicial
    "outro",
}

# -----------------------------
# Substncias / categorias amplas
# -----------------------------

ALLOWED_SUBSTANCES: set[str] = {
    # Classes farmacolgicas amplas
    "corticoide",
    "antihistaminico",
    "antibiotico",
    "imunossupressor",

    # Cuidados com a pele
    "hidratante",
    "sabao_neutro",

    # Alternativos / no farmacolgicos
    "fitoterapico",
    "oleo_natural",

    # Quando no  possvel classificar
    "outro",
}

# -----------------------------
# Resposta percebida pelo usurio
# -----------------------------

ALLOWED_RESPONSES: set[str] = {
    # Percepo clara de melhora
    "melhora",

    # Algum alvio, mas sintomas persistem
    "melhora_parcial",

    # Nenhuma mudana percebida
    "sem_resposta",

    # Piora percebida aps uso
    "piora",

    # Relato menciona uso, mas no descreve resultado
    "desconhecida",
}
