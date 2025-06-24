# API dermasync

## Description - English

This repository contains the backend service for the DermaSync project ([www.dermasync.com.br](https://www.dermasync.com.br)) — a platform designed to extract and deliver insights from the collective experiences of people living with atopic dermatitis.

It implements a Retrieval-Augmented Generation (RAG) pipeline that processes user-generated content from online communities (such as Facebook, Telegram, and Reddit). Using semantic vector embeddings, the system retrieves relevant segments and generates actionable insights to support patients in making informed decisions about their treatment.

The backend API for the DermaSync project. It is modularly organized to handle:
- Image upload and processing
- Processing of user reports
- Enrichment using LLMs
- Integration with a vector database (ChromaDB)

## 🏗️ Project initial structure

/app
/routes
├── imagens.py
├── relatos.py
└── usuario.py
/services
├── imagens_service.py
├── chroma_service.py
└── enriquecimento_service.py
/main.py

## Estrutura do Projeto

<!-- ESTRUTURA_INICIO -->
```
├── Dockerfile
├── Dockerfile.overlay
├── README.md
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── endpoints.py
│   │   ├── endpoints_lomadee.py
│   │   ├── endpoints_mercadolivre.py
│   │   ├── endpoints_videos.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   ├── services
│   │   │   ├── mercadolivre
│   │   │   │   ├── auth.py
│   │   │   │   ├── mercadolivre.py
│   │   │   │   ├── produtos.py
│   │   │   │   ├── usuarios.py
│   ├── auth
│   │   ├── dependencies.py
│   │   ├── schemas.py
│   ├── chroma
│   │   ├── buscador_segmentos.py
│   │   ├── buscador_tags.py
│   │   ├── factory.py
│   │   ├── ingest_from_jsonl.py
│   ├── config.py
│   ├── firestore
│   │   ├── client.py
│   ├── llm
│   │   ├── gemini.py
│   ├── logger_config.py
│   ├── main.py
│   ├── pipeline
│   │   ├── B_enriquecimento
│   │   │   ├── enriquecer_metadados.py
│   │   │   ├── extrair_detalhes_terapeuticos.py
│   │   │   ├── extrair_tags_llm.py
│   │   │   ├── gerar_microdepoimento.py
│   │   ├── a_extracao_bruta
│   │   │   ├── gerar_jsonl_bruto.py
│   │   ├── dados
│   │   │   ├── jsonl_brutos
│   │   │   │   ├── relatos-20250529.jsonl
│   │   │   │   ├── relatos-20250608.jsonl
│   │   │   │   ├── relatos-20250609-v.jsonl
│   │   │   │   ├── relatos-20250609.jsonl
│   │   │   │   ├── relatos-20250620-facebook-v0.0.1.jsonl
│   │   │   │   ├── relatos-20250620-facebook-v1.0.0.jsonl
│   │   │   ├── jsonl_enriquecidos
│   │   │   │   ├── relatos-20250620-facebook-v0.0.1.enriquecido.jsonl
│   │   │   │   ├── relatos_enriquecidos-20250529.jsonl
│   │   │   │   ├── relatos_enriquecidos-20250609-n.jsonl
│   │   │   │   ├── relatos_enriquecidos-20250609-v.jsonl
│   │   │   │   ├── relatos_enriquecidos-20250609.jsonl
│   │   │   ├── relatos_recebidos.jsonl
│   │   │   ├── segmentos
│   │   │   │   ├── segmentos-20250529.jsonl
│   │   ├── data_reader.py
│   │   ├── llm_client
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── gemini_client.py
│   │   ├── scripts
│   │   │   ├── 01_gerar_jsonl_bruto.py
│   │   │   ├── 02_enriquecer_metadados.py
│   │   │   ├── 03_segmentar_para_vetores.py
│   │   │   ├── 04_rag_chroma.py
│   │   │   ├── __init__.py
│   │   │   ├── _llm_client
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── gemini_client.py
│   │   │   ├── corrige.py
│   ├── routes
│   │   ├── imagens.py
│   │   ├── relatos.py
│   ├── schema
│   │   ├── relato.py
│   │   ├── relato_schema.json
│   ├── services
│   │   ├── imagens_service.py
│   │   ├── relatos_service.py
├── atualizar_readme_estrutura.py
├── clean_docker_cache.bat
├── deploy_dermasync_api.bat
├── docs
│   ├── arquitetura-dermasync.png
│   ├── decisao_17062025.md
│   ├── decisao_19052025.md
├── requirements-v3.txt
├── requirements.txt
├── run_tests.py
├── static
│   ├── imagens
│   │   ├── 231ea371-f20d-48bf-bb4e-4eb205fd45f1.png
│   │   ├── a53544c2-91d6-4872-b6ca-00c9dd5b9ac4.png
├── temp_storage
│   ├── teste_integra_0_57a4169f.jpg
│   ├── teste_integra_0_a23f89b9.jpg
│   ├── teste_integra_0_e2255201.jpg
├── test_report.md
├── tree.py
```
<!-- ESTRUTURA_FIM -->