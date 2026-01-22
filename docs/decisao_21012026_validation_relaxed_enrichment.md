# Decisão Arquitetural  
## Validação Relaxada no Enrichment Cognitivo (Schema v2)

**Data:** 21/01/2026  
**Status:** Aceita  
**Projeto:** DermaSync  
**Escopo:** Pipeline de Enrichment Cognitivo (`EXTRACT_COMPUTABLE_METADATA`)  

---

## 1. Contexto

O projeto **DermaSync** utiliza modelos de linguagem (LLMs) para extrair metadados computáveis a partir de relatos textuais de usuários, com foco em dermatite atópica.

Esses metadados são estruturados conforme o **schema v2**, que define vocabulários controlados para:

- `tags`
- `signals`
- `therapies`
- `body_regions`
- `temporal_markers`

Inicialmente, a validação desses campos foi projetada para ser **estrita (STRICT)**, rejeitando qualquer valor fora dos vocabulários definidos.

Durante a integração com um **modelo LLM local (Gemma 3 via Ollama)**, observou-se que:

- O modelo gera **JSON estruturalmente correto**
- O modelo respeita o contrato cognitivo geral
- O modelo apresenta **alucinações lexicais pontuais**, como:
  - `descamação` vs `descamacao`
  - `escurimento_pele` vs `escurecimento_pele`
  - `face` quando não previsto em `ALLOWED_BODY_REGIONS`

Essas variações não representam erro semântico grave, mas quebram a validação estrita e interrompem o pipeline.

---

## 2. Problema

Manter validação estrita desde o início implicaria:

- Bloqueio frequente do pipeline de enrichment
- Dificuldade de evolução arquitetural (RAG, embeddings, UX)
- Correções prematuras de LLM antes de haver dados suficientes
- Mistura indevida entre problemas lexicais e problemas arquiteturais

Por outro lado, remover completamente a validação resultaria em:

- Perda de governança semântica
- Dados não auditáveis
- Impossibilidade de reprocessamento futuro confiável

Era necessário um **meio-termo técnico controlado**.

---

## 3. Decisão

Foi decidido introduzir **modos explícitos de validação semântica** no schema v2:

### 3.1 Modos de validação

- **STRICT**
  - Rejeita qualquer valor fora do vocabulário
  - Garante máxima consistência semântica
  - Indicado para pipelines maduros e reprocessamentos finais

- **RELAXED**
  - Permite valores fora do vocabulário
  - Preserva o dado bruto gerado pelo LLM
  - Mantém estrutura, tipagem e contrato do schema
  - Utilizado durante desenvolvimento e integração inicial

> **Validação relaxada não é ausência de validação.  
É uma política explícita, rastreável e reversível.**

---

## 4. Ponto de aplicação da decisão

### 4.1 Boundary arquitetural

A escolha do `validation_mode` ocorre no:

EnrichMetadataService

yaml
Copiar código

Justificativa:

- É o boundary entre o LLM imperfeito e o domínio interno
- O schema não deve decidir política de ambiente
- O repositório não deve conter lógica cognitiva

---

### 4.2 Propagação explícita para persistência

O `validation_mode` é persistido em dois níveis:

#### a) Documento de enrichment (Firestore)

```json
{
  "relato_id": "...",
  "version": "v2",
  "validation_mode": "relaxed",
  "data": { ... },
  "created_at": "..."
}
b) EffectResult (execução do pipeline)
json
Copiar código
{
  "effect_type": "EXTRACT_COMPUTABLE_METADATA",
  "success": true,
  "metadata": {
    "validation_mode": "relaxed",
    "model": "llm-gemma-3-local"
  }
}
Isso garante auditabilidade semântica e operacional.

5. Consequências e trade-offs
Benefícios
Pipeline cognitivo não bloqueia

Evolução arquitetural desacoplada da qualidade do LLM

Preservação integral dos dados

Possibilidade de reprocessamento futuro

Medição objetiva da maturidade do sistema

Custos assumidos
Dados RELAXED podem conter ruído lexical

Não devem ser tratados como “golden data”

Requer reprocessamento futuro para STRICT

Esses custos são explícitos e mensuráveis.

6. Métricas e governança
Foi introduzida a seguinte métrica técnica:

Percentual de enrichments RELAXED vs STRICT

Exemplo:

json
Copiar código
{
  "total": 120,
  "relaxed": 94,
  "strict": 26,
  "relaxed_pct": 78.33
}
Essa métrica permite:

Definir critérios objetivos de maturidade

Criar alertas técnicos

Decidir quando endurecer a validação

7. Estratégia de longo prazo
Esta decisão é temporária e intencional.

Ela habilita:

Normalização semântica leve
(ex: descamação → descamacao)

Job de reprocessamento em STRICT
(batch sobre dados históricos)

Comparação empírica entre RELAXED e STRICT

Evolução para modelos mais robustos ou fine-tuning

8. Princípios arquiteturais preservados
Mesmo com validação RELAXED:

O schema permanece central

O vocabulário continua sendo referência

O erro é rastreável

O sistema permanece determinístico

Nenhuma gambiarra estrutural foi introduzida

9. Conclusão
A adoção de validação RELAXED no enrichment cognitivo é uma decisão técnica consciente que:

Preserva rigor arquitetural

Desacopla qualidade do modelo e qualidade do sistema

Mantém governança semântica

Permite evolução incremental e auditável

Essa decisão posiciona o DermaSync como um sistema de IA aplicado com maturidade técnica e visão de longo prazo.