# app/llm/prompts/enrich_metadata_prompt.py

def build_enrich_metadata_prompt(relato_text: str) -> str:

    if not relato_text or not relato_text.strip():
        raise ValueError("Relato vazio ou inválido para enriquecimento.")

    return f"""
Extraia os dados do relato e retorne APENAS JSON válido.

REGRAS:
- sem markdown
- sem comentários
- sem texto extra
- não inventar dados
- lowercase
- sem duplicatas em listas
- usar null quando ausente
- manter exatamente as chaves abaixo

SCHEMA:
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
  "resumo_publico": null
}}

REGRAS SEMÂNTICAS:
- idade: número inteiro representando a idade do paciente, se mencionada. Exemplo: "45 anos" -> 45
  - se a idade for expressa em meses, bebê, recém-nascido etc, coloque idade = null e preencha faixa_etaria com "bebê", "criança", "adolescente", "adulto jovem", "adulto", "idoso" conforme apropriado
- genero:
  - homem -> masculino
  - mulher -> feminino
  - ambíguo -> null
- sintomas:
  - apenas sintomas físicos/dermatológicos
  - usar termos curtos
  - exemplo: "coceira intensa" -> "coceira"
- tratamentos_mencionados:
  - medicamentos, terapias ou práticas
  - exemplo: hidratante, corticoide, banho morno
- regioes_afetadas:
  - partes do corpo mencionadas
  - usar termos curtos
  - exemplo: "braços e pernas" -> ["braços", "pernas"]
- temporal_markers:
  - indicadores de tempo mencionados
  - usar termos curtos
  - exemplo: "desde ontem" -> ["ontem"]
- titulo_resumido:
  - resumo de uma frase do relato, focando no principal sintoma ou situação
  - exemplo: "Minha pele está coçando muito com bolhas nas mãos" -> "coceira intensa com bolhas nas mãos"
- solucao_encontrada:
  - se o relato mencionar uma solução ou melhora, resumir em uma frase curta
  - exemplo: "Depois de usar um creme hidratante e tomar Metrexato, minha pele melhorou" -> "melhora com creme hidratante e imunossupressor"
- resumo_publico:
  - Resumo curto até 3 frases explicando os sintomas e situação, e o que foi tentado e resultado obtido. Sem mencionar marcas de produtos.
  - exemplo: "Tive coceira e ardência nas pernas, então eu usei hidratante Cerave e tomei corticoide oral" -> "Paciente com coceira e ardência nas pernas, teve melhora com hidratante e corticoide oral."

RELATO:
{relato_text}
""".strip()