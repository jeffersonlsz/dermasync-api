# Domain · Galeria  
## Política de Leitura e Elegibilidade Cognitiva

Este módulo define o **núcleo conceitual da leitura de relatos no DermaSync**.

Ele **não trata de UI**, **não trata de infraestrutura**, **não trata de autenticação técnica**.  
Seu papel é modelar **como experiências humanas podem ser legitimamente expostas a outros humanos**, sob critérios éticos, semânticos e cognitivos.

---

## Princípio Fundamental

> **Relatos não são dados brutos.  
> Relatos são narrativas situadas.  
> A galeria não exibe relatos — ela media leitura.**

Toda decisão aqui responde à pergunta:

> *“Este humano pode, deve e em que condições entrar em contato com esta narrativa?”*

---

## Escopo do Módulo

Este domínio é responsável por:

- Modelar **quem é o leitor**, do ponto de vista cognitivo
- Modelar **como o relato deseja ser visto**
- Decidir **se um relato é elegível para leitura**
- Declarar **condições mínimas de similaridade**
- Produzir **decisões explicáveis**, auditáveis e versionáveis

Este módulo **não**:
- calcula embeddings
- acessa banco de dados
- conhece UI
- conhece frameworks web
- interpreta permissões técnicas (JWT, OAuth, etc.)

---

## Conceitos Centrais

### 1. UserCognitiveProfile

Representa o **leitor enquanto agente cognitivo**, não enquanto entidade técnica.

Ele expressa:
- papel no sistema (user, collaborator, admin)
- existência ou não de um relato-base
- nível de exposição desejado à diversidade de experiências

> ⚠️ *ExposureLevel não é permissão.  
> É apetite cognitivo.*

---

### 2. RelatoVisibilityPolicy

Cada relato carrega sua própria política de visibilidade.

Isso garante que:
- decisões éticas possam evoluir
- consentimentos possam ser reforçados
- mudanças de UX não exijam migração de dados

A política define:
- status do relato (approved, anonymized, etc.)
- restrições explícitas de leitura

> Um relato **não é passivo**:  
> ele declara como pode ser lido.

---

### 3. RelatoEligibilityDecision

Resultado explícito e estruturado de uma decisão de elegibilidade.

Nunca usamos booleanos soltos.

Toda decisão deve ser:
- justificável
- registrável
- traduzível em UX Effects
- auditável no futuro

---

### 4. RelatoEligibilityService

Serviço de domínio **puro**, responsável por aplicar as regras.

Ele:
- não consulta banco
- não calcula similaridade
- não conhece UI
- não faz logging técnico

Ele apenas declara:
- se o relato é elegível
- se similaridade é exigida
- qual o limiar mínimo
- por quê

---

## Separação Conceitual Importante

| Conceito | Pertence a |
|--------|-----------|
| Identidade técnica | auth / users |
| Relato como entidade | domain/relato |
| Leitura e exposição | domain/galeria |
| Similaridade vetorial | camada de busca (C) |
| Forma visual | camada de UI (D) |

Misturar essas camadas gera:
- decisões opacas
- acoplamento ético
- fragilidade arquitetural

---

## Relação com UX Effects

Este domínio **não gera UX Effects diretamente**.

Mas toda `RelatoEligibilityDecision`:
- é traduzível em UX Effects
- fornece justificativa semântica
- sustenta confiança do usuário

A UI **interpreta**, o domínio **justifica**.

---

## Filosofia de Design

Este módulo segue os princípios de:

- **Arquitetura Cognitiva**  
- **DDD orientado a significado**
- **Ética por construção**
- **Explicabilidade como requisito**
- **Separação radical de responsabilidades**

Qualquer mudança neste domínio deve responder:

> *“Estamos protegendo melhor o humano que lê e o humano que escreveu?”*

Se a resposta não for clara, a mudança está errada.

---

## Status

- Versão: v1
- Estável para testes de domínio
- Evolutivo por versionamento explícito