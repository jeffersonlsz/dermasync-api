# app/domain/enrichment/prompts/extract_computable_metadata_v2.py

from app.domain.enrichment.vocabularies.tags_v1 import ALLOWED_TAGS
from app.domain.enrichment.vocabularies.signals_v1 import (
    ALLOWED_SIGNALS,
    ALLOWED_INTENSITIES,
    ALLOWED_FREQUENCIES,
)
from app.domain.enrichment.vocabularies.therapies_v1 import (
    ALLOWED_THERAPY_TYPES,
    ALLOWED_SUBSTANCES,
    ALLOWED_RESPONSES,
)
from app.domain.enrichment.vocabularies.body_regions_v1 import ALLOWED_BODY_REGIONS
from app.domain.enrichment.vocabularies.temporal_markers_v1 import (
    ALLOWED_TEMPORAL_MARKERS,
)

PROMPT_VERSION = "extract_computable_metadata_v2_structured"


def build_prompt(relato_text: str) -> str:
    """
    Prompt otimizado para extração de metadados clínicos estruturados.
    Versão 2 - Foco em clareza, estrutura XML e regras explícitas.

    Estratégias:
    - Persona clara e específica.
    - Estrutura com tags XML-like para delimitar seções.
    - Instruções consolidadas e regras de "o que não fazer" explícitas.
    - Guia para o score de confiança.
    - Schema e vocabulários controlados mantidos.
    """

    prompt_template = f"""
<system_goal>
Você é um analista de dados clínicos especializado em dermatologia. Sua tarefa é extrair informações estruturadas de um relato de paciente e formatá-las como um único objeto JSON. Aderir estritamente ao schema e vocabulários fornecidos é mandatório.
</system_goal>

<rules>
1.  **Formato de Saída**: Sua única saída deve ser um objeto JSON válido, começando com `{{` e terminando com `}}`.
2.  **Sem Texto Adicional**: Não inclua nenhum texto, explicação, ou markdown (como ` ```json `) antes ou depois do JSON.
3.  **Aderência ao Schema**: Siga exatamente o schema JSON fornecido na seção `<output_schema>`. Não invente, remova ou altere campos.
4.  **Vocabulário Controlado**: Utilize APENAS os valores exatos das listas `ALLOWED_*` fornecidas na seção `<allowed_vocabularies>`. A grafia deve ser idêntica.
5.  **Campos Vazios**: Se nenhuma informação relevante for encontrada para um campo que espera uma lista (ex: "tags", "signals"), retorne uma lista vazia `[]`. Para campos de string (ex: resumos), retorne uma string vazia `""` se não aplicável.
6.  **Booleanos**: Não use valores booleanos (`true`/`false`).
7.  **Score de Confiança**: O campo `extraction` em `confidence` deve ser um float entre 0.0 e 1.0, refletindo sua confiança na precisão da extração. Use 1.0 para certeza total, 0.5 para incerteza moderada, e 0.1 para baixa confiança.
</rules>

<allowed_vocabularies>
  - ALLOWED_TAGS: {", ".join(sorted(ALLOWED_TAGS))}
  - ALLOWED_SIGNALS: {", ".join(sorted(ALLOWED_SIGNALS))}
  - INTENSITY: {", ".join(sorted(ALLOWED_INTENSITIES))}
  - FREQUENCY: {", ".join(sorted(ALLOWED_FREQUENCIES))}
  - THERAPY_TYPE: {", ".join(sorted(ALLOWED_THERAPY_TYPES))}
  - SUBSTANCE: {", ".join(sorted(ALLOWED_SUBSTANCES))}
  - RESPONSE: {", ".join(sorted(ALLOWED_RESPONSES))}
  - BODY_REGIONS: {", ".join(sorted(ALLOWED_BODY_REGIONS))}
  - TEMPORAL_MARKERS: {", ".join(sorted(ALLOWED_TEMPORAL_MARKERS))}
</allowed_vocabularies>

<output_schema>
{{
  "version": "v2",
  "computable": {{
    "tags": ["string"],
    "signals": [
      {{ "signal": "string", "intensity": "string", "frequency": "string" }}
    ],
    "therapies": [
      {{ "type": "string", "substance": "string", "response": "string" }}
    ],
    "body_regions": ["string"],
    "temporal_markers": ["string"]
  }},
  "summaries": {{
    "public": "string",
    "clinical": "string"
  }},
  "confidence": {{
    "extraction": 0.0
  }}
}}
</output_schema>

<example>
<input_text>
Paciente relata piora da pele com o sol e estresse. Usa pomada Protopic de vez em quando para coceira leve no rosto, que melhora bem.
</input_text>
<output_json>
{{
  "version": "v2",
  "computable": {{
    "tags": ["exposicao_solar", "fator_emocional"],
    "signals": [
      {{ "signal": "prurido", "intensity": "baixa", "frequency": "ocasional" }}
    ],
    "therapies": [
      {{ "type": "topico", "substance": "inibidor_calcineurina", "response": "melhora_total" }}
    ],
    "body_regions": ["face"],
    "temporal_markers": []
  }},
  "summaries": {{
    "public": "Relato de paciente com piora da pele devido ao sol e estresse, com tratamento para coceira no rosto.",
    "clinical": "Prurido facial de baixa intensidade e frequência ocasional, com boa resposta a inibidor de calcineurina tópico. Gatilhos incluem sol e estresse."
  }},
  "confidence": {{
    "extraction": 0.9
  }}
}}
</output_json>
</example>

<text_to_analyze>
{relato_text}
</text_to_analyze>

<final_instruction>
Agora, analise o relato do paciente na seção `<text_to_analyze>` e gere o objeto JSON correspondente.
</final_instruction>
"""
    return prompt_template.strip()