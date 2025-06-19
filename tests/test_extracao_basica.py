import pytest
"""
Tests for the Dermasync API extraction functionality.
This module contains unit tests to validate the behavior of the LLM client instantiation
and basic functionality checks. Additionally, it includes commented-out tests for JSON 
schema validation and data extraction, which can be enabled in the future.
Functions:
- test_instancia_llm: Validates that the LLM client is instantiated correctly.
- test_primeiro_test: A placeholder test to ensure basic assertion functionality.
- test_extracao_conforme_schema (commented): Validates the extracted data against a 
    predefined JSON schema and checks the correctness of the extracted content.
Notes:
- The `test_extracao_conforme_schema` function is currently commented out and requires 
    the `extrair_dados` function from the `my_pipeline.extrator` module to be implemented 
    and imported.
- The JSON schema (`esquema_json`) defines the expected structure for the extracted data.
"""
import jsonschema
#from my_pipeline.extrator import extrair_dados
from app.pipeline.scripts.llm_client.base import get_llm_client   
# Schema mínimo de contrato JSON
esquema_json = {
    "type": "object",
    "properties": {
        "genero": {"type": "string"},
        "idade": {"type": "integer"},
        "sintomas": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tratamentos": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["genero", "idade", "sintomas"]
}

# 
def test_instancia_llm():
    llm_client = get_llm_client('gemini')
    assert llm_client is not None

def test_primeiro_test():
    assert 1 == 1

