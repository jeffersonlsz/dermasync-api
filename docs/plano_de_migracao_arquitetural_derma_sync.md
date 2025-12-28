# Plano de Migração Arquitetural do DermaSync

Este documento formaliza **as fases de migração progressiva**, testável e sem quebra de comportamento, para consolidar a arquitetura baseada em **Domínio + Orquestrador + Intenções + Estados + Adaptadores**.

O objetivo não é reescrever o sistema, mas **torná-lo governável**, explicável e extensível — um *Domain Cognitive Engine*.

---

## 1. Visão Arquitetural Geral

### Princípio Central

> **O domínio decide. Os adaptadores executam.**

O DermaSync passa a operar como um sistema em camadas cognitivas claras:

```
[ Mundo Externo ]
   │
   ▼
[ Adapters ]  ← FastAPI · Firebase · Jobs · LLMs
   │
   ▼
[ Orchestrator de Domínio ]
   │
   ▼
[ Estados · Intenções · Guards · Transições ]
```

Nada fora do domínio decide regras de negócio.

---

## 2. Camada de Domínio (Core Cognitivo)

### Local
```
app/domain/relato/
```

### Responsabilidade
Representar **a verdade semântica** do sistema:
- O que é um relato
- Em que estado ele está
- O que pode acontecer com ele
- Sob quais condições

### Arquivos Canônicos

```
app/domain/relato/
├── states.py        # Estados possíveis do relato
├── intents.py       # Intenções semânticas
├── guards.py        # Regras determinísticas
├── transitions.py  # Mapa explícito intent → estado
├── contracts.py    # Tipos (Context, Decision, Effect)
├── effects.py      # Tipos de efeitos (ordens)
└── orchestrator.py # Cérebro único de decisão
```

### Restrições Fortes
- ❌ Não importa FastAPI
- ❌ Não importa Firebase
- ❌ Não chama LLM
- ❌ Não faz IO

O domínio **apenas decide**.

---

## 3. Orchestrator (Cérebro Executivo)

### Função
Receber uma **intenção** e decidir:
- se é permitida
- qual o próximo estado
- quais efeitos devem ocorrer

### Assinatura Conceitual

```
Decision = f(intent, state, context)
```

### O que ele faz
1. Valida contrato
2. Executa guards
3. Avalia transição
4. Retorna Decision

### O que ele NÃO faz
- Não grava banco
- Não chama services
- Não executa jobs

---

## 4. Camada de Adaptadores

### Local
```
app/routes/
app/services/
app/firestore/
app/llm/
```

### Responsabilidade
- Traduzir mundo externo → domínio
- Executar efeitos ordenados pelo domínio

### Exemplo de Fluxo

```
HTTP POST /relatos
   ↓
Route
   ↓
Orchestrator.attempt_intent(...)
   ↓
Decision(effects=[ProcessarRelato])
   ↓
Service executa ProcessarRelato
```

---

## 5. Plano de Migração Progressiva

### FASE 0 — Congelamento (mapa mental)
⏱ 1–2h

Objetivo:
- Não alterar comportamento
- Mapear decisões existentes

Ações:
- Listar intents reais
- Listar estados reais
- Identificar onde decisões estão espalhadas

Entrega:
- Diagrama simples intent → estado → efeito

---

### FASE 1 — Consolidação do Domínio (sem impacto)
⏱ 3–4h

Objetivo:
- Domínio existe formalmente
- Não governa nada ainda

Ações:
- Finalizar states.py, intents.py, guards.py
- Criar contracts.py (Context, Decision)
- Garantir testes de domínio verdes

Risco: **zero**

---

### FASE 2 — Orchestrator como Juiz (decide, não executa)
⏱ 4–6h

Objetivo:
- Toda decisão passa pelo domínio

Ações:
- Unificar orchestrator.py + relato_intent_orchestrator.py
- Orchestrator retorna Decision
- Routes chamam orchestrator antes de services

Services continuam executando como antes.

---

### FASE 3 — Services viram Executores
⏱ 1–2 dias

Objetivo:
- Services não decidem mais

Ações:
- Criar effects.py
- Mover lógica de decisão de services → domínio
- Services apenas executam efeitos

Exemplos:
- ProcessarRelatoEffect
- AnonimizarRelatoEffect
- IndexarRelatoEffect

---

### FASE 4 — Limpeza Estrutural
⏱ 3–4h

Objetivo:
- Remover código morto

Ações:
- Deletar relato_executor.py
- Remover if/else duplicados
- Simplificar rotas

---

## 6. Garantias que essa Arquitetura Dá

- Testes determinísticos por intenção
- Ética codificada (guards)
- Estado rastreável
- Evolução segura
- LLM como ferramenta, não oráculo

---

## 7. Critério de Sucesso

O DermaSync deixa de ser:
> “um backend com LLM”

E passa a ser:
> **um sistema cognitivo de domínio, com memória, causalidade e ética explícita**.

---

**Próximo passo**: Unificar `orchestrator.py` e `relato_intent_orchestrator.py` em um único cérebro canônico.

