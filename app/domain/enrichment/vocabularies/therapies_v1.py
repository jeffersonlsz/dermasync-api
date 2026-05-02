# app/domain/enrichment/vocabularies/therapies_v1.py

"""
Vocabulário controlado de terapias relatadas pelo usuário.

Este módulo define APENAS categorias computáveis de intervenções mencionadas
em relatos humanos. Não representa prescrição médica, recomendação clínica
ou eficácia terapêutica real.

Regras:
- Vocabulário fechado (adições exigem versionamento)
- Sem marcas comerciais
- Sem dosagens
- Sem inferência clínica
- Baseado em percepção do usuário
"""

# -----------------------------
# Tipos de intervenção
# -----------------------------

ALLOWED_THERAPY_TYPES: set[str] = {
    # Aplicações na pele
    "topico",

    # Medicamentos ingeridos
    "oral",

    # Rotina de higiene / cuidados com a pele
    "higienico",

    # Mudanças de hábito ou comportamento
    "comportamental",

    # Quando o relato menciona algo fora do escopo inicial
    "outro",
}

# -----------------------------
# Substâncias / categorias amplas
# -----------------------------

ALLOWED_SUBSTANCES: set[str] = {
    # Classes farmacológicas amplas
    "corticoide",
    "antihistaminico",
    "antibiotico",
    "imunossupressor",

    # Cuidados com a pele
    "hidratante",
    "sabao_neutro",

    # Alternativos / não farmacológicos
    "fitoterapico",
    "oleo_natural",

    # Quando não é possível classificar
    "outro",
}

# -----------------------------
# Resposta percebida pelo usuário
# -----------------------------

ALLOWED_RESPONSES: set[str] = {
    # Percepção clara de melhora
    "melhora",

    # Algum alívio, mas sintomas persistem
    "melhora_parcial",

    # Nenhuma mudança percebida
    "sem_resposta",

    # Piora percebida após uso
    "piora",

    # Relato menciona uso, mas não descreve resultado
    "desconhecida",
}
