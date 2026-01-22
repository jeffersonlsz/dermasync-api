# tests/domain/enrichment/test_enriched_metadata_v2_validator.py

import pytest
from app.domain.enrichment.schemas.enriched_metadata_v2 import EnrichedMetadataV2

VALID_PAYLOAD = {
    "version": "v2",
    "computable": {
        "tags": ["dermatite_atopica", "coceira"],
        "signals": [
            {
                "signal": "prurido",
                "intensity": "alta",
                "frequency": "diaria"
            }
        ],
        "therapies": [
            {
                "type": "topico",
                "substance": "corticoide",
                "response": "melhora_parcial"
            }
        ],
        "body_regions": ["dobra_cotovelo"],
        "temporal_markers": ["cronico"]
    },
    "summaries": {
        "public": "Relato descreve sintomas recorrentes de dermatite.",
        "clinical": "Prurido intenso em dobras com resposta parcial a corticoide."
    },
    "confidence": {
        "extraction": 0.85
    }
}

def test_valid_payload_passes_validation():
    model = EnrichedMetadataV2.model_validate(VALID_PAYLOAD)
    assert model.version == "v2"
    assert model.confidence.extraction == 0.85

def test_extra_field_fails():
    payload = VALID_PAYLOAD | {"unexpected": "boom"}

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)

def test_invalid_tag_fails():
    payload = VALID_PAYLOAD.copy()
    payload["computable"]["tags"] = ["dermatite_atopica", "alien_skin"]

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)


def test_invalid_signal_fails():
    payload = VALID_PAYLOAD.copy()
    payload["computable"]["signals"][0]["signal"] = "telepatia"

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)

def test_invalid_body_region_fails():
    payload = VALID_PAYLOAD.copy()
    payload["computable"]["body_regions"] = ["joelho_direito"]

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)

def test_confidence_out_of_range_fails():
    payload = VALID_PAYLOAD.copy()
    payload["confidence"]["extraction"] = 1.5

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)


def test_summary_too_long_fails():
    payload = VALID_PAYLOAD.copy()
    payload["summaries"]["public"] = "a" * 500

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)


def test_missing_required_field_fails():
    payload = VALID_PAYLOAD.copy()
    del payload["computable"]["signals"]

    with pytest.raises(Exception):
        EnrichedMetadataV2.model_validate(payload)

