import pytest
from unittest.mock import patch, MagicMock
from app.llm.enrich_metadata_runner import run_enrich_metadata_llm, _parse_llm_response

def test_run_enrich_metadata_llm_empty_relato():
    with pytest.raises(ValueError, match="Relato vazio ou invÃÂ¡lido."):
        run_enrich_metadata_llm("")

    with pytest.raises(ValueError, match="Relato vazio ou invÃÂ¡lido."):
        run_enrich_metadata_llm("   ")

@patch("app.llm.enrich_metadata_runner.OllamaClient")
@patch("app.llm.enrich_metadata_runner.build_enrich_metadata_prompt")
def test_run_enrich_metadata_llm_success(mock_build_prompt, mock_ollama_client):
    # Setup mocks
    mock_prompt = "Mock prompt"
    mock_build_prompt.return_value = mock_prompt
    
    mock_llm_instance = MagicMock()
    mock_ollama_client.return_value = mock_llm_instance
    
    mock_json_response = '{"key": "value"}'
    mock_llm_instance.generate.return_value = mock_json_response
    
    # Execution
    relato = "Valid relato text"
    result = run_enrich_metadata_llm(relato)
    
    # Asserts
    mock_build_prompt.assert_called_once_with(relato)
    mock_ollama_client.assert_called_once()
    mock_llm_instance.generate.assert_called_once_with(prompt=mock_prompt)
    assert result == {"key": "value"}

@patch("app.llm.enrich_metadata_runner.OllamaClient")
def test_run_enrich_metadata_llm_invalid_json(mock_ollama_client):
    mock_llm_instance = MagicMock()
    mock_ollama_client.return_value = mock_llm_instance
    
    # Retorna uma string que nÃÂ£o ÃÂ© um JSON vÃÂ¡lido
    mock_llm_instance.generate.return_value = "Not a JSON"
    
    with pytest.raises(ValueError, match="Falha ao parsear resposta do LLM:"):
        run_enrich_metadata_llm("Valid relato text")

@patch("app.llm.enrich_metadata_runner.OllamaClient")
def test_run_enrich_metadata_llm_not_dict_json(mock_ollama_client):
    mock_llm_instance = MagicMock()
    mock_ollama_client.return_value = mock_llm_instance
    
    # Retorna uma lista em vez de dict
    mock_llm_instance.generate.return_value = '["Not", "a", "dict"]'
    
    with pytest.raises(ValueError, match="Resposta do LLM nÃÂ£o retornou JSON vÃÂ¡lido."):
        run_enrich_metadata_llm("Valid relato text")

def test_parse_llm_response_valid():
    # Testa _parse_llm_response com e sem markdown
    response_with_markdown = "```json\n{\"id\": 123}\n```"
    assert _parse_llm_response(response_with_markdown) == {"id": 123}

    response_without_markdown = "{\"id\": 123}"
    assert _parse_llm_response(response_without_markdown) == {"id": 123}

def test_parse_llm_response_thinking_output():
    # Testa parsing de output com "Thinking..." e escapes ANSI
    thinking_response = (
        'Thinking...\nThinking Process:\n\n'
        '1.  **Analyze the Request:** The goal is to act as a deterministic semantic\x1b[8D\x1b[K\n'
        'semantic extraction system and convert the provided text into a strictly va\x1b[2D\x1b[K\n'
        'valid JSON format based on a specific schema and set of rules.\n\n'
        '{"idade": null,"genero": null,"sintomas": ["dermatite atópica","coceira"],'
        '"tratamentos_mencionados": ["hidratar a pele"]}'
    )
    
    expected_dict = {
        "idade": None,
        "genero": None,
        "sintomas": ["dermatite atópica", "coceira"],
        "tratamentos_mencionados": ["hidratar a pele"]
    }
    
    assert _parse_llm_response(thinking_response) == expected_dict

def test_parse_llm_response_invalid():
    with pytest.raises(ValueError, match="Falha ao parsear resposta do LLM:"):
        _parse_llm_response("invalid text")
