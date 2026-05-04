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
    Prompt otimizado para extrao de metadados clnicos estruturados.
    Verso 2 - Foco em clareza, estrutura XML e regras explcitas.

    Estratgias:
    - Persona clara e especfica.
    - Estrutura com tags XML-like para delimitar sees.
    - Instrues consolidadas e regras de "o que no fazer" explcitas.
    - Guia para o score de confiana.
    - Schema e vocabulrios controlados mantidos.
    """

    prompt_template = f"""
<system_goal>
Voc  um analista de dados clnicos especializado em dermatologia. Sua tarefa  extrair informaes estruturadas de um relato de paciente e format-las como um nico objeto JSON. Aderir estritamente ao schema e vocabulrios fornecidos  mandatrio.
</system_goal>

<rules>
1.  **Formato de Sada**: Sua nica sada deve ser um objeto JSON vlido, comeando com `{{` e terminando com `}}`.
2.  **Sem Texto Adicional**: No inclua nenhum texto, explicao, ou markdown (como ` ```json `) antes ou depois do JSON.
3.  **Aderncia ao Schema**: Siga exatamente o schema JSON fornecido na seo `<output_schema>`. No invente, remova ou altere campos.
4.  **Vocabulrio Controlado**: Utilize APENAS os valores exatos das listas `ALLOWED_*` fornecidas na seo `<allowed_vocabularies>`. A grafia deve ser idntica.
5.  **Campos Vazios**: Se nenhuma informao relevante for encontrada para um campo que espera uma lista (ex: "tags", "signals"), retorne uma lista vazia `[]`. Para campos de string (ex: resumos), retorne uma string vazia `""` se no aplicvel.
6.  **Booleanos**: No use valores booleanos (`true`/`false`).
7.  **Score de Confiana**: O campo `extraction` em `confidence` deve ser um float entre 0.0 e 1.0, refletindo sua confiana na preciso da extrao. Use 1.0 para certeza total, 0.5 para incerteza moderada, e 0.1 para baixa confiana.
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
    "clinical": "Prurido facial de baixa intensidade e frequncia ocasional, com boa resposta a inibidor de calcineurina tpico. Gatilhos incluem sol e estresse."
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
Agora, analise o relato do paciente na seo `<text_to_analyze>` e gere o objeto JSON correspondente.
</final_instruction>
"""
    return prompt_template.strip()
