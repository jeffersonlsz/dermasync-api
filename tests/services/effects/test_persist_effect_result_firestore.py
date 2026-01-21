import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.effects.persist_firestore import persist_effect_result_firestore
from app.services.effects.result import EffectResult

def test_persist_effect_result_firestore_accepts_uuid_fields():
    """
    Garantia arquitetural:
    - UUIDs NÃO podem vazar como objetos para o Firestore
    - Persistência NÃO pode lançar exceção
    """

    fake_result = EffectResult(
        relato_id=uuid.uuid4(),
        effect_type="PERSIST_RELATO",
        effect_ref=uuid.uuid4(),
        success=True,
        metadata={
            "image_id": uuid.uuid4(),
            "attempt": 1,
        },
        error=None,
        executed_at=datetime.utcnow(),
    )

    fake_collection = MagicMock()
    fake_doc = MagicMock()
    fake_collection.document.return_value = fake_doc

    fake_db = MagicMock()
    fake_db.collection.return_value = fake_collection

    with patch(
        "app.services.effects.persist_firestore.get_firestore_client",
        return_value=fake_db,
    ):
        # 🚨 ESTE CALL DEVE FALHAR HOJE
        # 🚨 E PASSAR APÓS A CORREÇÃO
        persist_effect_result_firestore(fake_result)

    # Se chegou até aqui, NÃO lançou exceção
    assert True


def test_persist_effect_result_firestore_rejects_raw_uuid_values():
    """
    Contrato:
    - Nenhum uuid.UUID pode chegar cru ao Firestore
    - Persistência deve normalizar antes de set()
    """

    fake_result = EffectResult(
        relato_id=uuid.uuid4(),
        effect_type="PERSIST_RELATO",
        effect_ref=uuid.uuid4(),
        success=True,
        metadata={
            "image_id": uuid.uuid4(),
        },
        error=None,
        executed_at=datetime.utcnow(),
    )

    def firestore_set_strict(data):
        def walk(value):
            if isinstance(value, uuid.UUID):
                raise TypeError("Firestore cannot accept uuid.UUID")
            if isinstance(value, dict):
                for v in value.values():
                    walk(v)
            if isinstance(value, list):
                for v in value:
                    walk(v)

        walk(data)

    fake_doc = MagicMock()
    fake_doc.set.side_effect = firestore_set_strict

    fake_collection = MagicMock()
    fake_collection.document.return_value = fake_doc

    fake_db = MagicMock()
    fake_db.collection.return_value = fake_collection

    with patch(
        "app.services.effects.persist_firestore.get_firestore_client",
        return_value=fake_db,
    ):
        persist_effect_result_firestore(fake_result)


def test_persist_effect_result_firestore_normalizes_uuid_before_persisting():
    """
    Contrato forte:
    - UUIDs DEVEM ser convertidos antes de chegar ao Firestore
    """

    fake_result = EffectResult(
        relato_id=uuid.UUID("0f8e6e03-12aa-402a-8346-e1684de998b3"),
        effect_type="PERSIST_RELATO",
        effect_ref=uuid.UUID("11111111-2222-3333-4444-555555555555"),
        success=True,
        metadata={
            "image_id": uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        },
        error=None,
        executed_at=datetime.utcnow(),
    )

    captured_data = {}

    def firestore_set_strict(data):
        # se chegar UUID cru, explode
        def walk(value):
            if isinstance(value, uuid.UUID):
                raise TypeError("UUID leaked to Firestore")
            if isinstance(value, dict):
                for v in value.values():
                    walk(v)
            if isinstance(value, list):
                for v in value:
                    walk(v)

        walk(data)
        captured_data.update(data)

    fake_doc = MagicMock()
    fake_doc.set.side_effect = firestore_set_strict

    fake_collection = MagicMock()
    fake_collection.document.return_value = fake_doc

    fake_db = MagicMock()
    fake_db.collection.return_value = fake_collection

    with patch(
        "app.services.effects.persist_firestore.get_firestore_client",
        return_value=fake_db,
    ):
        persist_effect_result_firestore(fake_result)

    # 🔥 Agora validamos semanticamente
    assert isinstance(captured_data["relato_id"], str)
    assert isinstance(captured_data["effect_ref"], str)
    assert isinstance(captured_data["metadata"]["image_id"], str)
