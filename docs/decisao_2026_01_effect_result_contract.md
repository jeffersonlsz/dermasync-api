# Decisão Arquitetural — UXEffect com Helpers Semânticos

**Data:** 2026-01  
**Contexto:** DermaSync — Arquitetura de UX Effects e Progress

---

## Contexto

O DermaSync utiliza **UX Effects** como protocolo semântico entre o domínio
e a interface do usuário. Esses efeitos não representam lógica de negócio,
mas sim **mensagens interpretáveis por humanos**, mediadas pela UI.

Durante a consolidação do contrato de `EffectResult`, tornou-se necessário
definir o papel exato de `UXEffect` no sistema.

---

## Decisão

Foi decidido que:

> **`UXEffect` será um Value Object imutável que pode conter helpers semânticos
> puros, sem dependência de contexto externo.**

Esses helpers não executam lógica de negócio e não acessam serviços, bancos
ou estados globais.

---

## Exemplos de Helpers Permitidos

- `is_blocking()`
- `is_terminal()`
- `affects_progress()`
- `requires_user_action()`

Esses métodos operam exclusivamente sobre os próprios campos do `UXEffect`,
como `type`, `severity`, `channel` e `timing`.

---

## Justificativa

### Por que não deixar toda a interpretação na UI?

- Geraria duplicação de lógica
- Aumentaria risco de inconsistência semântica
- Tornaria a UI mais complexa e frágil

### Por que não misturar lógica de negócio?

- Violaria separação de responsabilidades
- Tornaria efeitos dependentes de cont
