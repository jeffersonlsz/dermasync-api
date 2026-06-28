# Inventario da infraestrutura atual de LLM

Este documento registra o estado atual da infraestrutura de LLM do DermaSync antes
da migracao incremental para uma camada minima de orquestracao. Ele deve ser usado
como referencia para preservar comportamento, reaproveitar componentes existentes e
evitar abstracoes sem consumidor real.

Raiz analisada:

`D:\workspace_projects_001\dermasync\dermasync-api`

## Componentes atuais

### OllamaClient

Arquivo: `app/pipeline/llm_client/ollama_client.py`

Responsabilidade atual:

- Implementa `LLMClient`.
- Envia prompts para a API local do Ollama em `http://localhost:11434/api/generate`.
- Usa `OLLAMA_MODEL_NAME` vindo de `app.config`.
- Retorna apenas o texto em `result["response"]`.

Acoplamentos atuais:

- Endpoint do Ollama esta hardcoded no client.
- O modelo e resolvido por configuracao global, mas o runner instancia o client
  diretamente.
- O formato de request/response e especifico do Ollama.

Uso atual:

- `app/llm/enrich_metadata_runner.py`
- `app/llm/anonymous_content_runner.py`

### GeminiClient

Arquivo: `app/pipeline/llm_client/gemini_client.py`

Responsabilidade atual:

- Configura `google.generativeai` com `GEMINI_API_KEY`.
- Cria `genai.GenerativeModel(model_name)`.
- Envia prompt por `generate_content`.
- Retorna `response.text.strip()`.

Acoplamentos atuais:

- Configuracao do SDK ocorre dentro do client.
- O metodo publico e `completar(prompt)`, diferente de `OllamaClient.generate(prompt)`.
- A dependencia do SDK do Gemini fica diretamente no client de pipeline.

Uso atual:

- `app/pipeline/llm_client/base.py`, via `get_llm_client("gemini", nome_modelo)`.
- `app/pipeline/B_enriquecimento/enriquecer_metadados.py`, no fluxo legado de
  enriquecimento em JSONL.

### LLMClient e factory legada

Arquivo: `app/pipeline/llm_client/base.py`

Responsabilidade atual:

- Define a classe abstrata `LLMClient` com `generate(prompt: str) -> str`.
- Expoe `get_llm_client(provedor, nome_modelo)`.

Limitacoes atuais:

- A factory decide provider por `if/elif`.
- Gemini nao implementa o mesmo metodo definido pelo contrato (`generate`).
- Nao existem metadados de tarefa, formato de resposta, temperatura ou limites.
- Nao ha suporte a fallback, politicas ou multiplos adapters por contrato uniforme.

### LLMOutputParser

Arquivo: `app/application/parsers/llm/parser.py`

Responsabilidade atual:

- Remove ANSI.
- Extrai bloco JSON.
- Corrige problemas comuns de JSON.
- Converte resposta de metadados para `Metadata`.
- Faz reparo de JSON chamando novamente o LLM recebido no construtor.
- Extrai conteudo anonimizado a partir de resposta JSON.

Ponto importante para migracao:

- Deve ser reaproveitado.
- Hoje depende de um objeto com metodo `generate(prompt)`.
- Pode continuar funcionando com um adapter de compatibilidade ou com a nova porta
  de inferencia, desde que exista um consumidor real.

### RetryEngine

Arquivo: `app/application/effects/retry_engine.py`

Responsabilidade atual:

- Decide se um `EffectResult` com erro deve virar `RETRYING` ou erro final.
- Usa `RetryClassifier` e `RetryPolicy`.
- Atualiza metadados com tentativa, tipo de falha e intervalo de retry.

Ponto importante para migracao:

- Deve ser reaproveitado para efeitos/jobs.
- Nao deve ser confundido com retry interno de provider LLM, que ainda nao sera
  implementado nesta etapa.

### RetryPolicy

Arquivo: `app/application/effects/retry_policy.py`

Responsabilidade atual:

- Define contrato `RetryPolicy`.
- Implementa `DefaultRetryPolicy`.
- Decide retry por tipo de falha e numero de tentativa.

Ponto importante para migracao:

- Deve permanecer como politica de retry de efeitos existentes.
- Nao introduzir politica de roteamento LLM neste momento.

### RetryClassifier

Arquivo: `app/application/effects/retry_classifier.py`

Responsabilidade atual:

- Classifica falhas em tipos como `NETWORK_ERROR`, `TIMEOUT`,
  `PERMISSION_DENIED`, `INVALID_INPUT`, `STORAGE_TEMPORARY` e `UNKNOWN`.

Ponto importante para migracao:

- Deve ser preservado.
- Pode futuramente inspirar classificacao de falhas de provider, mas isso nao deve
  ser implementado antes de haver dois providers operando pelo mesmo contrato.

### EffectResult

Arquivo: `app/application/effects/result.py`

Responsabilidade atual:

- Value object imutavel para fatos de execucao.
- Estados: `STARTED`, `SUCCESS`, `ERROR`, `RETRYING`.
- Carrega metadata tecnica, erro e `retry_after`.

Uso atual no fluxo LLM:

- `EnrichMetadataJob` registra inicio, retry, sucesso e erro.
- `EffectResultRepository` persiste os resultados.

Ponto importante para migracao:

- Deve ser reaproveitado para observabilidade de job.
- Informacoes de inferencia podem ser adicionadas em `metadata` posteriormente,
  depois que os runners trabalharem internamente com `LLMResponse`.

### PipelineManager

Arquivo: `app/application/pipeline/manager.py`

Responsabilidade atual:

- Gerencia lease/claim de tarefas no Firestore.
- Evita processamento concorrente indevido da mesma tarefa.
- Marca tarefa como `PROCESSING`, `PROCESSED`, `RETRY` ou `DEAD_LETTER`.
- Detecta e reseta tarefas orfas.

Uso atual no fluxo LLM:

- `EnrichMetadataJob` usa `claim_task`, `complete_task` e `fail_task`.

Ponto importante para migracao:

- Deve ser preservado.
- Nao faz parte da abstracao de provider LLM.

### Jobs

Arquivo principal: `app/jobs/enrich_metadata_job.py`

Responsabilidade atual:

- Recebe `relato_id`.
- Faz claim da tarefa de enriquecimento.
- Busca relato.
- Registra `EffectResult.started`.
- Chama `run_enrich_metadata_llm`.
- Persiste metadados enriquecidos em `EnrichedMetadataRepository`.
- Monta payload com metadados e enrichment.
- Chama `generate_anonymous_content`.
- Atualiza `conteudo_anonimizado`.
- Completa a tarefa no pipeline.
- Registra sucesso ou falha.

Acoplamento indireto atual:

- O job nao instancia `OllamaClient` diretamente.
- O acoplamento a provider ocorre nos runners chamados pelo job.

Ponto importante para migracao:

- Nao modificar job no mesmo commit que migrar runner.
- Primeiro runner passa a usar `LLMInferencePort`.
- Depois runner passa a trabalhar com `LLMResponse`.
- Apenas depois o job consome metadados adicionais.

### Prompt builders

Arquivos atuais:

- `app/llm/prompts/enrich_metadata_prompt.py`
- `app/llm/prompts/anonymous_content_prompt.py`
- `app/domain/enrichment/prompts/extract_computable_metadata_v1.py`
- `app/domain/enrichment/prompts/extract_computable_metadata_v2.py`

Responsabilidade atual:

- Montam prompts para extracao semantica, enriquecimento e anonimimizacao.
- Prompts de dominio usam vocabularios controlados de enrichment.

Ponto importante para migracao:

- Devem ser reaproveitados.
- A nova porta de LLM deve receber o prompt ja construido.
- A aplicacao declara a intencao via `LLMTask`, nao via nome de modelo.

### Schemas e validadores

Arquivos principais:

- `app/domain/enrichment/schemas/enriched_metadata_v2.py`
- `app/domain/enrichment/schemas/base.py`
- `app/domain/enrichment/validation_mode.py`
- `app/domain/enrichment/validation/*`
- `app/domain/enrichment/vocabularies/*`

Responsabilidade atual:

- Definem schema de enrichment v2.
- Validam tags, regioes corporais e marcadores temporais.
- Controlam modo de validacao relaxed/strict.

Ponto importante para migracao:

- Devem ser preservados.
- Nao fazem parte do provider adapter.
- Continuam sendo consumidores da resposta normalizada do LLM.

### Configuracoes existentes

Arquivos:

- `app/config.py`
- `app/core/settings.py`

Configuracoes atuais relacionadas a LLM:

- `GEMINI_API_KEY`
- `OLLAMA_MODEL_NAME`, default atual em `app/config.py`
- `LLM_TEMPERATURE`
- `settings.LLM_MODEL`, default atual em `app/core/settings.py`

Risco atual:

- Ha mais de uma fonte de nome de modelo.
- O job registra `settings.LLM_MODEL`, enquanto `OllamaClient` usa
  `OLLAMA_MODEL_NAME`.
- Isso pode gerar divergencia entre modelo usado e modelo registrado.

## Fluxo completo atual da inferencia em runtime

### Enriquecimento de metadados

1. `EnrichMetadataJob.run(relato_id)` inicia o processamento.
2. `PipelineManager.claim_task` tenta reservar a tarefa.
3. `RelatoRepository.get_by_id` carrega o relato.
4. `EffectResult.started` e persistido.
5. O job chama `run_enrich_metadata_llm(relato["conteudo_original"])`.
6. `run_enrich_metadata_llm` valida texto vazio.
7. `build_enrich_metadata_prompt` cria o prompt.
8. O runner instancia `OllamaClient()` diretamente.
9. O runner instancia `LLMOutputParser(llm)`.
10. `OllamaClient.generate(prompt)` chama a API local do Ollama.
11. `LLMOutputParser.parse_metadata(response)` normaliza e valida a resposta.
12. Se o parse falhar, `LLMOutputParser` pede reparo ao mesmo client LLM.
13. O runner retorna `dict` de metadados.
14. O job salva o enrichment em `EnrichedMetadataRepository`.

### Geracao de conteudo anonimizado

1. O job monta payload com `metadados` e `enrichment`.
2. O job chama `generate_anonymous_content(payload)`.
3. `build_prompt` monta o prompt de anonimimizacao.
4. O runner instancia `OllamaClient()` diretamente.
5. O runner instancia `LLMOutputParser(llm)`.
6. `OllamaClient.generate(prompt)` chama a API local do Ollama.
7. `LLMOutputParser.parse_anonymous_content(response)` extrai o JSON.
8. O runner retorna o conteudo anonimizado.
9. O job atualiza `data.conteudo_anonimizado`.

### Fluxo legado de pipeline JSONL

1. `app/pipeline/B_enriquecimento/enriquecer_metadados.py` chama
   `get_llm_client("gemini", MODELO_LLM)`.
2. A factory cria `GeminiClient`.
3. O pipeline chama `client.completar(prompt)`.
4. A resposta e normalizada por `strip_code_fences`.
5. O JSON e parseado e incorporado no relato enriquecido.

## Problemas arquiteturais atuais

- Runners conhecem provider concreto (`OllamaClient`).
- Contratos de client nao sao uniformes (`generate` vs `completar`).
- Factory legada mistura selecao por string com criacao de client.
- Nao existe objeto de request que carregue tarefa, temperatura, max tokens,
  formato de resposta e metadados.
- Nao existe resposta normalizada com provider/model/task.
- Configuracoes de modelo estao duplicadas.
- Observabilidade de job existe, mas observabilidade de inferencia ainda nao.

## Diretriz para a migracao

Proximo passo permitido:

- Criar a abstracao minima `LLMInferencePort`, `LLMRequest`, `LLMResponse` e
  `LLMTask`.

O que nao deve ser implementado ainda:

- Roteamento por custo.
- Fallback.
- Rate limiting.
- Quotas.
- Circuit breaker.
- Cache.
- Telemetria avancada.
- Provider registry completo.

