from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user


client = TestClient(app)


def fake_user():
    class User:
        id = "user-123"
        role = "admin"

    return User()


app.dependency_overrides[get_current_user] = fake_user


@patch(
    "app.application.relatos.generate_anonymous_content_use_case.GenerateAnonymousContentUseCase.execute",
    new_callable=AsyncMock,
)
def test_generate_anonymous_content(
    mock_execute,
):
    mock_execute.return_value = {
        "relato_id": "relato-123",
        "conteudo_anonimizado": (
            "Mulher de 34 anos relatou coceira intensa. "
            "O tratamento incluiu hidratação da pele."
        ),
    }

    response = client.post(
        "/relatos/relato-123/anonimizar",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["relato_id"] == "relato-123"

    assert (
        body["conteudo_anonimizado"]
        == "Mulher de 34 anos relatou coceira intensa. "
        "O tratamento incluiu hidratação da pele."
    )

    mock_execute.assert_awaited_once_with(
        relato_id="relato-123",
    )