# Política de Similaridade Composicional no DermaSync
Uma abordagem epistemicamente explícita para mediação de narrativas humanas

## 1. Introdução

Sistemas baseados em relatos humanos frequentemente utilizam similaridade vetorial direta como critério primário para recomendação, filtragem ou agrupamento de narrativas. Embora eficaz do ponto de vista estatístico, essa abordagem apresenta limitações críticas quando aplicada a domínios sensíveis, como saúde, sofrimento corporal e experiência subjetiva.

O projeto DermaSync adota uma abordagem alternativa: a Similaridade Composicional, cujo objetivo não é apenas aproximar textos semanticamente, mas mediar o contato entre humanos de forma ética, explicável e cognitivamente controlada.

Este documento descreve os fundamentos teóricos, arquiteturais e computacionais dessa política.

## 2. Problema de Pesquisa

A pergunta central que orienta este trabalho é:

**Como definir similaridade entre narrativas humanas de forma explicável, controlável e auditável, evitando decisões opacas baseadas exclusivamente em embeddings?**

Subproblemas derivados incluem:

- Como evitar que um único vetor represente indevidamente experiências complexas?
- Como permitir ajuste fino da exposição cognitiva sem reprocessar todo o sistema?
- Como justificar, para o usuário, por que certos relatos são exibidos e outros não?

## 3. Limitações da Similaridade Vetorial Direta

A similaridade vetorial tradicional (ex.: cosine similarity entre embeddings):

- colapsa múltiplas dimensões semânticas em um único espaço
- não distingue quais aspectos são semelhantes
- não permite ponderação ética explícita
- dificulta explicação ao usuário final
- torna auditoria retrospectiva praticamente inviável

Em contextos sensíveis, essa opacidade representa risco técnico, ético e comunicacional.

## 4. Princípio da Similaridade Composicional

O DermaSync adota o seguinte princípio:

> **Similaridade não é proximidade geométrica.**
> **Similaridade é acordo semântico sob critérios explícitos.**

Assim, a similaridade total entre dois relatos é definida como a combinação ponderada de múltiplos eixos semânticos independentes, cada um representando uma dimensão compreensível da experiência humana.

## 5. Eixos de Similaridade

Os eixos representam dimensões interpretáveis, e não mecanismos de cálculo. Exemplos incluem:

- Sintomas relatados
- Região corporal afetada
- Faixa etária
- Resposta a terapias
- Padrões temporais
- Tom narrativo / emocional

Cada eixo produz um score parcial normalizado (0.0 – 1.0), podendo ser calculado via:

- regras simbólicas
- classificadores
- embeddings especializados
- LLMs supervisionados

O método de cálculo é externo à política composicional.

## 6. Política de Similaridade (Pesos)

A importância relativa de cada eixo é definida por uma política versionada, representada como um conjunto de pesos cuja soma é 1.0.

Essa política:

- é explícita
- é validável
- pode evoluir ao longo do tempo
- não exige reprocessamento dos dados históricos
- pode ser auditada e comparada entre versões

Formalmente:

`SimilarityScore = Σ (score_eixo_i × peso_eixo_i)`

## 7. Determinismo e Explicabilidade

A Similaridade Composicional é determinística:

- mesma política
- mesmos scores parciais
- mesmo resultado final

Além disso, o sistema preserva o breakdown por eixo, permitindo:

- explicação ao usuário (“esses relatos foram escolhidos porque…”)
- geração de UX Effects narrativos
- logging semântico
- auditoria ética posterior

## 8. Separação Arquitetural

A política de similaridade é explicitamente separada de:

- bancos vetoriais (ex.: ChromaDB)
- camada de infraestrutura
- lógica de UI
- autenticação e permissões técnicas

Essa separação garante que decisões cognitivas não fiquem acopladas a escolhas de stack.

## 9. Integração com Elegibilidade Cognitiva

A Similaridade Composicional não decide sozinha o que é exibido.

Ela opera em conjunto com:

- Política de Elegibilidade de Relatos
- Perfil Cognitivo do Usuário
- Nível de Exposição desejado

O resultado final é uma mediação cognitiva, não uma recomendação automática.

## 10. Implicações Éticas

Ao tornar explícitos os critérios de similaridade, o sistema:

- reduz vieses implícitos
- permite revisão consciente de decisões
- evita exposição excessiva ou inadequada
- respeita o caráter situado das narrativas humanas

A ética deixa de ser um “pós-processamento” e passa a ser estrutural.

## 11. Conclusão

A Similaridade Composicional proposta no DermaSync oferece uma alternativa robusta à similaridade vetorial direta, especialmente em domínios onde a experiência humana não pode ser reduzida a proximidade estatística.

Ao combinar explicabilidade, versionamento, determinismo e separação arquitetural, o modelo permite construir sistemas de IA mais responsáveis, auditáveis e alinhados à cognição humana.

## 12. Status do Documento

- **Versão:** C2 / v1
- **Natureza:** técnico-conceitual
- **Uso previsto:**
    - documentação arquitetural
    - base para artigo acadêmico curto
    - referência de design