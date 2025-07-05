# File: tests/test_parser_metrics.py
# tests/test_parser_metrics.py
# -*- coding: utf-8 -*-
# Este módulo contém testes para o parser de logs, gerador de diagramas Mermaid e métricas de latência.


import json

import pytest

from app.archlog_sync.mermaid_generator import to_sequence_diagram
from app.archlog_sync.metrics import compute_avg_latency, detect_slow_calls
from app.archlog_sync.parser import parse_logs


# Fixture: carregando os 4 eventos de exemplo
@pytest.fixture
def sample_events():
    path = "app/archlog_sync/exemplos/relato_log.jsonl"
    groups = parse_logs(path)
    return groups["req_001"]


def test_parse_logs_groups(sample_events):
    # Deve ser exatamente 4 entradas para req_001
    assert len(sample_events) == 4


def test_mermaid_generator(sample_events):
    diagram = to_sequence_diagram(sample_events).splitlines()
    # Primeira linha: sequência Mermaid
    assert diagram[0] == "sequenceDiagram"
    # Verifica uma das linhas geradas
    assert "frontend->>relato_service: POST /enviar-relato" in diagram


def test_compute_avg_latency(sample_events):
    avg = compute_avg_latency(sample_events)
    # Valores conhecidos: (122 + 321 + 1522 + 88) / 4 = 513.25
    assert pytest.approx(avg, rel=1e-3) == 513.25


def test_detect_slow_calls(sample_events):
    slow = detect_slow_calls(sample_events, threshold=1000)
    # Apenas a operação extrair_tags (1522 ms) ultrapassa 1000
    assert len(slow) == 1
    assert slow[0]["operation"] == "extrair_tags"
