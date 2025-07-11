# File: tests/test_archlog_sync_extra.py
# -*- coding: utf-8 -*-
# Este módulo contém testes adicionais para o parser de logs, gerador de diagramas Mermaid e métricas de latência.
# Ele inclui casos de erro, verificações de ordem e testes de métricas específicas.


import json
import logging

import pytest

from app.archlog_sync import logger, mermaid_generator, metrics, parser

logger = logging.getLogger(__name__)


# 1) Teste de erro ao abrir arquivo inexistente
def test_parse_logs_file_not_found():
    with pytest.raises(FileNotFoundError):
        parser.parse_logs("app/archlog_sync/exemplos/nao_existe.jsonl")


# 2) parse_logs: agrupamento de 0 eventos retorna dicionário vazio
def test_parse_logs_empty(tmp_path):
    # cria um arquivo vazio
    p = tmp_path / "empty.jsonl"
    if p.exists():
        p.unlink()
    else:
        p.touch()
    logger.info(f"Criando arquivo vazio para teste: {p}")
    p.write_text("")
    groups = parser.parse_logs(str(p))
    assert isinstance(groups, dict)
    assert groups == {}


# 3) mermaid_generator: lista vazia deve gerar só o header
def test_mermaid_empty():
    diagram = mermaid_generator.to_sequence_diagram([])
    lines = diagram.splitlines()
    assert lines == ["sequenceDiagram"]


# 4) mermaid_generator: mantém ordem original - teste desativado por enquanto
def test_mermaid_order(sample_events):
    logger.info("Testando ordem de eventos no diagrama Mermaid")
    logger.info(f"Total de eventos no sample: {len(sample_events)}")
    logger.info(f"Tipo da variável sample_events: {type(sample_events)}")
    diagram = mermaid_generator.to_sequence_diagram(sample_events).splitlines()
    assert diagram[0] == "sequenceDiagram"
    assert diagram[1].startswith("frontend->>relato_service")
    assert diagram[-1].startswith("llm_extractor->>chromadb")


# 5) metrics: threshold de exatamente 1000 não conta como lento
def test_detect_slow_calls_edge():
    evs = [{"duration_ms": 1000}, {"duration_ms": 1001}]
    slow = metrics.detect_slow_calls(evs, threshold=1000)
    assert len(slow) == 1
    assert slow[0]["duration_ms"] == 1001


# 6) metrics: p50/p95/p99 básicos (podemos testar só p50 aqui)
def test_compute_avg_latency_simple():
    evs = [{"duration_ms": 10}, {"duration_ms": 30}]
    avg = metrics.compute_avg_latency(evs)
    assert avg == pytest.approx(20, rel=1e-6)
