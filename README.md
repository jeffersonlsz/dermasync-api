# DermaSync — README (Master)



## Sumário

1. Visão Geral
2. Diagrama de Arquitetura (Mermaid)
3. Estrutura de Pastas
4. Especificação da API (Endpoints principais)
5. Formatos de Dados (JSONL, schema e exemplo)
6. Pipeline: do relato bruto ao RAG
7. Requisitos & Dependências
8. Instalação e Execução Local
9. Docker / Docker Compose
10. Deploy (Cloud Run + Firebase Hosting)
11. Testes Automatizados & CI
12. Segurança, Privacidade e Ética
13. Operação e Monitoramento
14. Roadmap técnico & estimativas de complexidade
15. Contribuição, Code Style e PRs
16. Troubleshooting (problemas comuns)
17. Licença
18. Créditos & referências

---

# 1. Visão Geral

O **DermaSync** é uma plataforma orientada por IA para coleta e análise de relatos anônimos sobre dermatite atópica. O objetivo técnico é criar um pipeline confiável e auditável que: (1) receba relatos com imagens e texto, (2) enriqueça metadados com LLMs, (3) anonimiza dados sensíveis, (4) armazene segmentos e embeddings em uma base vetorial (ChromaDB) e metadados em NoSQL, e (5) entregue ao usuário casos semelhantes e dicas geradas por RAG.

**Princípios de projeto:** reproducibilidade, auditabilidade, privacidade por design, separação clara entre front-end e back-end, infra resiliente (containerizada), testes automatizados e documentação gerada automaticamente.

---

# 2. Diagrama de Arquitetura

```mermaid
flowchart LR
  subgraph Frontend
    F[Vue (Mobile-first)]
  end

  subgraph API
    A[FastAPI (Cloud Run)]
    UP[Upload Service] --> A
    PIPE[Pipeline LLM + RAG] --> A
  end

  subgraph Storage
    GCS[(GCS / Firebase Storage)]
    NoSQL[(Firestore / Postgres)]
    VDB[(ChromaDB - vetorial)]
  end

  F -->|HTTPS| A
  A -->|images| GCS
  A -->|metadata| NoSQL
  PIPE --> VDB
  PIPE --> NoSQL
  A -->|query semântica| VDB

  classDef infra fill:#f3f4f6,stroke:#111,stroke-width:1px
  class API,Storage,Frontend infra
```

**Resumo do fluxo:** Frontend envia relato (imagens + texto) → API valida e grava imagens em GCS → enqueue job de processamento → pipeline LLM extrai metadados e anonimiza → segmenta e gera embeddings → insere vetores em ChromaDB + metadados em NoSQL → Frontend requisita casos semelhantes e recebe cards personalizados.

---

# 3. Estrutura de Pastas

```text
/ (repo root)
  /frontend            # Vue 3 + Vite (mobile-first)
  /api                 # FastAPI app + pipeline
    /app
      /routers         # endpoints
      /services        # integração com LLMs, vetores, storage
      /models          # Pydantic models e schemas
      /pipeline        # scripts organizados (01_*, 02_*)\      /tests
  /infra               # terraform / deployment scripts / dockerfiles
  /docs                # documentação técnica e diagramas
  /scripts             # utilitários (migrations, seed, cleanup)
  Dockerfile
  docker-compose.yml
  README.md
```

**Observação:** refatore cada módulo com testes unitários e contratos Pydantic explícitos; isso facilita a auditabilidade e o mock em integração contínua.

---

# 4. Especificação da API — Endpoints Principais

> **Versionamento:** inclua `/v1` no path. Ex.: `/api/v1/relatos`.

### Autenticação
- `POST /api/v1/auth/login` — troca de token (OAuth / email+senha)
- `POST /api/v1/auth/external-login` — login por provedores (Google/Facebook)

### Relatos
- `POST /api/v1/relatos/completo` — envia relato com imagens + metadados brutos (público)
  - Body: multipart/form-data (fields: `json` + `files[]`)
  - Retorna: `{ id: str, status: 'received' }`
- `GET /api/v1/relatos/{id}` — obtém relato (somente metadados e referência a imagens)
- `GET /api/v1/relatos/similares/{id}?top_k=6` — busca casos semanticamente similares

### Galeria e Busca
- `GET /api/v1/galeria?filters=...&page=...` — paginação e filtros (idade, região, sintomas)
- `GET /api/v1/galeria/case/{id}` — detalhes do card

### Administração
- `GET /api/v1/admin/pending` — lista relatos pendentes para moderação
- `POST /api/v1/admin/approve/{id}` — aprova relato para exibição
- `POST /api/v1/admin/reject/{id}` — rejeita relato e registra motivo

**Contratos:** defina modelos Pydantic para todas as respostas e erros padrão (RFC-compliant), use OpenAPI (automatic docs via FastAPI).

---

# 5. Formatos de Dados

### 5.1 JSON Schema (simplificado) — Relato bruto

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RelatoBruto",
  "type": "object",
  "required": ["texto_relato", "idade_aproximada", "regiao_afetada", "consentimento"],
  "properties": {
    "texto_relato": {"type": "string"},
    "idade_aproximada": {"type": "string"},
    "regiao_afetada": {"type": "string"},
    "medicacoes": {"type": "array", "items": {"type": "string"}},
    "posologia": {"type": "string"},
    "consentimento": {"type": "boolean"},
    "metadados_local": {"type": "object"}
  }
}
```

### 5.2 Exemplo de instância (JSONL ready)

```jsonl
{"id":"r123","texto_relato":"Usei hidratante X por 2 semanas, melhorou levemente. A coceira diminuiu à noite.","idade_aproximada":"30-39","regiao_afetada":"braço direito","medicacoes":["hidratante X","corticosteroide tópico Y"],"posologia":"usar 2x/dia","consentimento":true}
```

### 5.3 Formato de metadados enriquecidos (após LLM)

```json
{
  "id": "r123",
  "anon_id": "anon_8f3a",
  "idade_estimada": 34,
  "genero_estimado": "masculino",
  "regiao_afetada": ["braço"],
  "sintomas_extraidos": ["coceira","vermelhidão"],
  "medicacoes_extraidas": [{"nome":"hidratante X","tipo":"OTC"}],
  "palavras_chave": ["coceira","melhora noturna"],
  "texto_original": "<hash ou referência ao storage — não o texto em claro>"
}
```

**Crucial:** o campo `texto_original` no metadado armazenado deve ser um **hash** ou **referência armazenada em GCS com acesso restrito**. Nunca gravar PII direto nos metadados públicos.

---

# 6. Pipeline — passos e responsabilidades

**Visão geral:** o pipeline é composto por módulos que correspondem a scripts numerados (seguindo a sua convenção):

1. `01_gerar_jsonl_bruto.py` — coleta dados do Firestore / uploads e gera arquivos `.jsonl` brutos.
2. `02_extrair_metadados.py` — chama LLM para extrair campos estruturados (idade, gênero, medicação etc.).
3. `03_anonimizar.py` — aplica regras e heurísticas (NLP + regex) para remover/obfuscar PII.
4. `04_segmentar_para_vetores.py` — segmentação semântica (sentenças + janelas deslizantes) para embeddings.
5. `05_rag_chroma.py` — grava embeddings em ChromaDB e metadados correlatos em NoSQL.

**Detalhes essenciais por etapa:**
- **Extração via LLM:** usar prompts com instruções claras, esquema de saída JSON, validação do JSON retornado e fallback para re-check (com poucas tentativas). Logar a versão do modelo e embed prompt tokens para auditoria.
- **Anonimização:**  dupla verificação — regras determinísticas (regex para emails, telefones, CPFs) + LLM para reconhecer PII contextual. Manter uma trilha de auditoria (hashes antes/depois) e nunca armazenar o texto original sem controle de acesso.
- **Segmentação:** use heurísticas: manter contexto médico relevante, evitar cortar frases médicas entre segmentos, limitar chunk a 300–700 tokens dependendo do encoder de embedding.
- **Embeddings & vetores:** padronizar modelo de embedding e armazenar metadata `embedding_version` e `text_version` no documento.

**Observabilidade:** cada job deve emitir métricas: tempo de processamento, porcentagem de erros de parsing, número de PII detectadas, tokens consumidos.

---

# 7. Requisitos & Dependências

**Mínimos:**
- Python 3.11+
- Node 18+
- Docker 24+
- Docker Compose

**Principais bibliotecas (ser cuidadoso com versões):**
- FastAPI
- Uvicorn
- Pydantic
- LangChain
- chromadb
- google-cloud-storage / firebase-admin
- sqlalchemy / asyncpg (se optar Postgres)
- pytest, pytest-asyncio

Inclua `requirements.txt` e `package.json` com versões fixas (sem `^` em produção) para reprodutibilidade.

---

# 8. Instalação e Execução Local

**Backend (api):**

```bash
git clone <repo>
cd api
python -m venv .venv
source .venv/bin/activate  # windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# ajustar variáveis no .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

**Observação:** para rodar localmente sem GCS/ChromaDB, mantenha `CHROMA_MODE=local` e `STORAGE_EMULATOR=true` nas variáveis de ambiente (ver .env.example).

---

# 9. Docker / Docker Compose

**Estrutura:** um `Dockerfile` para `api` e um para `frontend`. Um `docker-compose.yml` orquestra `api`, `db`(postgres), `chroma` (local) e `minio` (S3 emulado) para desenvolvimento onboard.

**Comandos:**

```bash
docker-compose build
docker-compose up -d
# logs
docker-compose logs -f api
```

**Melhor prática:** tratar secrets via Docker secrets ou usar local `.env` apenas para desenvolvimento; em staging/prod, use Secret Manager.

---

# 10. Deploy (Cloud Run + Firebase Hosting)

**Resumo recomendado:**
- Backend: build do container e deploy para Cloud Run (privado), revisado por CI.
- Frontend: build do Vite e deploy para Firebase Hosting com domínio `www.dermasync.com.br`.
- Storage: GCS (Buckets por ambiente) e regras de IAM restritas.

**Pipeline CI (sujestão):**
- PR -> rodar tests unitários + lint
- Build image -> push para Container Registry
- Deploy para staging (Cloud Run with traffic 0%)
- Smoke tests em staging -> promover para produção via job manual

**Exemplo comandos GCloud:**

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/dermasync-api:latest
gcloud run deploy dermasync-api --image gcr.io/<PROJECT_ID>/dermasync-api:latest --platform managed --region=us-central1 --allow-unauthenticated
```

(Ajuste `--allow-unauthenticated` conforme necessidade; recomenda-se `--no-allow-unauthenticated` para produção e front controlar o acesso.)

---

# 11. Testes Automatizados & CI

**Estrutura de testes:**
- `tests/unit/` — testes rápidos, mocks
- `tests/integration/` — testes que podem tocar DB local ou emulado (docker)
- `tests/e2e/` — smoke tests que rodam em staging

**Rodando apenas testes de relatos (exemplo):**

```bash
pytest -q tests/unit/test_relatos.py
# ou
pytest -q tests/unit/ -k relatos
```

**Cobertura:**

```bash
pytest --cov=app --cov-report=xml
```

**CI sugerido (GitHub Actions / GitLab CI):**
- `lint` (flake8/isort/ruff)
- `unit-tests` (pytest)
- `build` (docker build)
- `integration-tests` (run on docker-compose)
- `deploy` (manual approval)

---

# 12. Segurança, Privacidade e Ética

**Checklist obrigatório:**
- Anonimização: remover PII antes de qualquer armazenamento público.
- Consentimento: todo envio deve possuir `consentimento:true`. Logs de consentimento imutáveis com timestamp.
- Limitação de aconselhamento: disclaimers claros na UI — não substituir médicos.
- Tratamento de imagens: as imagens são processadas exclusivamente no backend; thumbnails públicas não devem conter metadados EXIF.
- Retenção: política clara (ex.: imagens mantidas 3 anos por padrão e passíveis de exclusão a pedido do usuário).
- Auditoria: armazenar versão do modelo LLM, prompt hash e timestamp para cada extração.
- Acesso: roles e permissões (admin, colaborador, moderador). Endpoints administrativos protegidos.

**Anonymization strategy:**
- Pipeline com regex deterministic + NER via LLM. Se LLM identificar PII, registrar e obfuscar.
- Manter cópia encriptada do original se for necessário para auditoria (acesso apenas admin com justificativa). Preferir não armazenar quando possível.

**Política de incidentes:**
- Log de incidentes e processo de notificação (ex.: e-mail + log em canal dedicado). Documentar e fixar PRs de correção.

---

# 13. Operação e Monitoramento

**Métricas mínimas:**
- Requests por minuto (API)
- Latência 95/99 percentil
- Jobs por hora (pipeline)
- Erros de parsing JSON (%)
- Tokens consumidos por modelo
- Casos com PII detectadas

**Alertas:**
- Latência média > 1s por request em produção
- Erros 5xx > 1% do tráfego
- Falha no job de ingestão por 3 runs consecutivos

**Logs:**
- Estruture logs JSON (timestamp, request_id, job_id, model_version, duration_ms)
- Correlacione via `request_id` entre API e jobs

---

# 14. Roadmap técnico & estimativas

**Sprint 0 — Infra & CI (10 dias)**
- Dockerize API & Frontend (3 dias)
- CI básico com lint + unit tests (2 dias)
- Deploy inicial para staging (Cloud Run) (3 dias)
- Observability baseline (metrics + logs) (2 dias)

**Sprint 1 — Pipeline básico (15 dias)**
- `01_gerar_jsonl_bruto` e `02_extrair_metadados` (6 dias)
- `03_anonimizar` (4 dias)
- `04_segmentar_para_vetores` + Chroma local (5 dias)

**Complexidade e critério de aceitação:**
- Cada etapa deve ter testes unitários e integração local. Critério de aceitação: `>90%` dos relatos processados sem erros de parsing em dataset de validação.

**Observação crítica:** estimativas assumem desenvolvedor sênior e infraestrutura já provisionada; ajustes podem duplicar prazos se houver bloqueios (ex.: quotas GCP, problemas de CORS, retrabalho por formato de imagem variado).

---

# 15. Contribuição, Code Style e PRs

**Guia rápido:**
- Fork → branch `feature/<short-desc>` → PR com descrição técnica e checklist
- Tests obrigatórios para features novas
- Lint e formatter passam antes do merge (ruff/black/isort)
- PRs pequenos: 200–400 linhas. PRs maiores devem ser divididos.

**Commit message convention:** use Conventional Commits:
- `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`

---

# 16. Troubleshooting

**Problema:** `chroma not reachable` — verifique `CHROMA_HOST` e rede do container.

**Problema:** `LLM JSON parse error` — verifique prompt e aumenta validação; reduzir temperatura e usar instrução `respond ONLY JSON`.

**Problema:** `images upload failed` — verifique quotas do GCS e permissões IAM do service account.

---

# 17. Licença

Sugestão: `MIT` para abrir colaboração, a menos que haja necessidade de restrição legal.

```
MIT License
<ano> Jefferson Leandro
```

---

# 18. Créditos & Referências

- LangChain docs
- ChromaDB docs
- Artigos sobre RAG e verificação factual
- Princípios de privacidade por design

---

## Anexos úteis (copiar/adaptar)

### .env.example

```
# General
ENV=development
PORT=8000

# GCP / Storage
GCS_BUCKET=dermasync-dev-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Chroma
CHROMA_MODE=local
CHROMA_HOST=http://localhost:8001

# Auth
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=...

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_VERSION=v1

# Feature flags
STORAGE_EMULATOR=true
```

### Exemplo de Prompt (extração de metadados — LLM)

```
You are an assistant specialized in extracting clinical-like structured data from user narratives about skin conditions.
Input: <raw_text>
Output: Strict JSON with keys: idade_aproximada (string), regioes (array), sintomas (array), medicacoes (array), posologia (string), consentimento (boolean)
Return only valid JSON. If uncertain, return null for the field.
```

---

## Notas finais do mentor

Jefferson — este README é um **artefato de confiança técnica**. Não o trate como marketing: mantenha sempre exemplos reais (jsonl) e versões de ferramentas (hash dos containers, imagens) para tornar o projeto auditável. Assim que colar este README no repo, gere também um `docs/architecture.md` com os diagramas e um `docs/pipeline.md` com logs de exemplo — estes arquivos tornam a revisão técnica muito mais rápida.

Se quer, eu posso:
- Gerar o `README.md` final com base neste documento (pronto para colar). ✅
- Criar `docs/pipeline.md` e `docs/architecture.md` automaticamente. ⚠️ (posso começar agora se desejar)

---

