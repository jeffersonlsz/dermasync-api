# File: app/archlog_sync/metrics.py
# -*- coding: utf-8 -*-
"""
Este módulo contém funções para calcular métricas de latência e detectar chamadas lentas a partir de eventos de log.
"""

def compute_avg_latency(events):
    return sum(e["duration_ms"] for e in events) / len(events)

def detect_slow_calls(events, threshold=1000):
    return [e for e in events if e["duration_ms"] > threshold]

if __name__ == "__main__":
    from .parser import parse_logs
    g = parse_logs("app/archlog_sync/exemplos/relato_log.jsonl")
    evs = g["req_001"]
    print("Avg:", compute_avg_latency(evs))
    print("Slow:", detect_slow_calls(evs))
