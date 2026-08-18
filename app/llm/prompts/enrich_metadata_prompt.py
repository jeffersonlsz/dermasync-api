# app/llm/prompts/enrich_metadata_prompt.py

# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido para enriquecimento.")

    return f"""
    Você é um extrator de conhecimento especializado em dermatologia.

    Sua única função é transformar o relato abaixo em um JSON estruturado.

    IMPORTANTE

    Retorne APENAS JSON válido.

    Não escreva explicações.

    Não escreva markdown.

    Não utilize ```.

    Não invente informações.

    Quando uma informação não puder ser inferida com segurança utilize:

    - null para campos únicos
    - [] para listas

    Nunca crie sintomas, tratamentos ou relações que não estejam explicitamente mencionados ou claramente implícitos no texto.

    Utilize português.

    Utilize lowercase sempre que possível.

    Não gere itens duplicados.

    ----------------------------------------
    SCHEMA
    ----------------------------------------

    {{
      "idade": null,
      "genero": null,
      "sintomas": [],
      "tratamentos_mencionados": [],
      "regioes_afetadas": [],
      "temporal_markers": [],
      "titulo_resumido": null,
      "solucao_encontrada": null,
      "faixa_etaria": null,
      "resumo_publico": null,

      "knowledge": {{

        "entities": {{

          "symptoms": [
            {{
              "id": "symptom_1",
              "name": "",
              "normalized_name": null,
              "severity": null,
              "frequency": null,
              "confidence": null
            }}
          ],

          "treatments": [
            {{
              "id": "treatment_1",
              "name": "",
              "category": null,
              "dosage": null,
              "frequency": null,
              "duration": null,
              "outcome": null,
              "confidence": null
            }}
          ],

          "triggers": [
            {{
              "id": "trigger_1",
              "name": "",
              "category": null,
              "confidence": null
            }}
          ],

          "affected_regions": [
            {{
              "id": "region_1",
              "body_part": "",
              "laterality": null,
              "confidence": null
            }}
          ],

          "outcomes": [
            {{
              "id": "outcome_1",
              "type": "",
              "description": null,
              "confidence": null
            }}
          ]

        }},

        "relations": [
          {{
            "source_id": "",
            "relation": "",
            "target_id": "",
            "confidence": null
          }}
        ],

        "timeline": [
          {{
            "id": "event_1",
            "event": "",
            "description": null,
            "approximate_date": null,
            "confidence": null
          }}
        ],

        "evidence": [
          {{
            "id": "evidence_1",
            "text": "",
            "confidence": null
          }}
        ],

        "extraction_metadata": {{
          "extractor_version": "knowledge_v1",
          "llm_model": null,
          "extracted_at": null
        }}

      }}

    }}

    ----------------------------------------
    REGRAS DOS CAMPOS LEGADOS
    ----------------------------------------

    idade

    - inteiro
    - somente se explicitamente informado

    genero

    - masculino
    - feminino
    - null

    sintomas

    - lista simples de sintomas
    - usar termos curtos

    tratamentos_mencionados

    - medicamentos
    - terapias
    - hábitos
    - práticas

    regioes_afetadas

    - partes do corpo

    temporal_markers

    - datas
    - períodos
    - duração
    - expressões temporais

    titulo_resumido

    - frase curta resumindo o caso

    solucao_encontrada

    - resumo curto da melhora encontrada

    resumo_publico

    - até 3 frases
    - sem marcas comerciais
    - sem informações pessoais

    ----------------------------------------
    REGRAS DO KNOWLEDGE
    ----------------------------------------

    ## Symptoms

    Extraia sintomas individualmente.

    Sempre que possível normalize.

    Exemplo

    "coceira muito forte"

    ↓

    name = "coceira"

    normalized_name = "prurido"

    severity = "alta"

    ## Treatments

    Extrair todos os tratamentos mencionados.

    Exemplos

    - hidratante
    - tacrolimo
    - corticoide
    - banho morno
    - fototerapia

    ## Triggers

    Extrair fatores desencadeantes.

    Exemplos

    - calor
    - suor
    - estresse
    - sabonete
    - poeira
    - alimentação

    ## Affected Regions

    Extrair regiões anatômicas.

    Separar regiões compostas.

    "braços e pernas"

    ↓

    ["braços","pernas"]

    ## Outcomes

    Extrair resultados.

    Exemplos

    - melhora
    - piora
    - remissão
    - recaída
    - controle parcial

    ## Relations

    Criar relações SOMENTE quando claramente suportadas pelo texto.

    Utilizar apenas estes verbos:

    CAUSES

    WORSENS

    IMPROVES

    TREATS

    PRECEDES

    FOLLOWS

    ASSOCIATED_WITH

    Exemplos

    Trigger

    CAUSES

    Symptom

    Treatment

    IMPROVES

    Symptom

    Treatment

    TREATS

    Outcome

    ## Timeline

    Criar eventos importantes na ordem cronológica.

    Exemplos

    Primeira crise

    Início do tratamento

    Melhora

    Recaída

    ## Evidence

    Guardar pequenos trechos literais do relato que sustentem as principais conclusões.

    Cada evidência deve conter apenas o trecho relevante.
    
    
    Lembre-se: não invente evidências. Se não houver evidência, use null. Confidence é sempre um número entre 0.0 e 1.0, representando a confiança na extração.
    
    ----------------------------------------
    RELATO
    ----------------------------------------

    {relato_text}
    """.strip()