# Effects Architecture — Commands vs Results

## Visão Geral

No DermaSync, efeitos são tratados em dois níveis semânticos distintos:

- **EffectCommand** → ordem executável
- **EffectResult** → registro histórico de uma execução passada

Misturar esses conceitos é um erro arquitetural.

---

## EffectCommand (Ação)

**Responsabilidade**
- Representa uma intenção de execução
- Pode ser emitido pelo domínio ou derivado de um retry
- Não contém sucesso, erro ou timestamps de execução

**Local**
- app/domain/effects/commands.py

**Características**
- Imutável
- Executável
- Efêmero (não é persistido como histórico)

---

## EffectResult (Memória)

**Responsabilidade**
- Representa o resultado de uma execução passada
- Usado para auditoria, UX, retry e explicabilidade
- Nunca deve ser executado diretamente

**Local**
- app/services/effects/result.py

**Características**
- Persistido
- Contém success, error, timestamps
- Não executável

---

## Regra Fundamental

> **Nenhum executor aceita EffectResult.**
> **Nenhum histórico vira ação sem conversão explícita.**

---

## Onde ocorre a conversão

A conversão `EffectResult → EffectCommand` ocorre **exclusivamente** em:

- `app/services/retry_relato.py`

Essa camada atua como **adaptador semântico**, não como executor.

---

## Imports Proibidos

- Domain **NÃO** importa services
- Executor **NÃO** importa EffectResult
- Infra **NÃO** conhece histórico
- Rotas **NÃO** decidem retry

---

## Consequência Arquitetural

Essa separação garante:
- retry seguro
- UX explicável
- testes determinísticos
- evolução sem regressão semântica
