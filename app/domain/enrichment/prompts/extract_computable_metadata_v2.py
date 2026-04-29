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
    Prompt otimizado para extraÃ§Ã£o de metadados clÃ­nicos estruturados.
    VersÃ£o 2 - Foco em clareza, estrutura XML e regras explÃ­citas.

    EstratÃ©gias:
    - Persona clara e especÃ­fica.
    - Estrutura com tags XML-like para delimitar seÃ§Ãµes.
    - InstruÃ§Ãµes consolidadas e regras de "o que nÃ£o fazer" explÃ­citas.
    - Guia para o score de confianÃ§a.
    - Schema e vocabulÃ¡rios controlados mantidos.
    """

    prompt_template = f"""
<system_goal>
VocÃª Ã© um analista de dados clÃ­nicos especializado em dermatologia. Sua tarefa Ã© extrair informaÃ§Ãµes estruturadas de um relato de paciente e formatÃ¡-las como um Ãºnico objeto JSON. Aderir estritamente ao schema e vocabulÃ¡rios fornecidos Ã© mandatÃ³rio.
</system_goal>

<rules>
1.  **Formato de SaÃ­da**: Sua Ãºnica saÃ­da deve ser um objeto JSON vÃ¡lido, comeÃ§ando com `{{` e terminando com `}}`.
2.  **Sem Texto Adicional**: NÃ£o inclua nenhum texto, explicaÃ§Ã£o, ou markdown (como ` ```json `) antes ou depois do JSON.
3.  **AderÃªncia ao Schema**: Siga exatamente o schema JSON fornecido na seÃ§Ã£o `<output_schema>`. NÃ£o invente, remova ou altere campos.
4.  **VocabulÃ¡rio Controlado**: Utilize APENAS os valores exatos das listas `ALLOWED_*` fornecidas na seÃ§Ã£o `<allowed_vocabularies>`. A grafia deve ser idÃªntica.
5.  **Campos Vazios**: Se nenhuma informaÃ§Ã£o relevante for encontrada para um campo que espera uma lista (ex: "tags", "signals"), retorne uma lista vazia `[]`. Para campos de string (ex: resumos), retorne uma string vazia `""` se nÃ£o aplicÃ¡vel.
6.  **Booleanos**: NÃ£o use valores booleanos (`true`/`false`).
7.  **Score de ConfianÃ§a**: O campo `extraction` em `confidence` deve ser um float entre 0.0 e 1.0, refletindo sua confianÃ§a na precisÃ£o da extraÃ§Ã£o. Use 1.0 para certeza total, 0.5 para incerteza moderada, e 0.1 para baixa confianÃ§a.
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
    "clinical": "Prurido facial de baixa intensidade e frequÃªncia ocasional, com boa resposta a inibidor de calcineurina tÃ³pico. Gatilhos incluem sol e estresse."
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
Agora, analise o relato do paciente na seÃ§Ã£o `<text_to_analyze>` e gere o objeto JSON correspondente.
</final_instruction>
"""
    return prompt_template.strip()
