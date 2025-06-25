from fastapi import APIRouter, Request
import httpx
from urllib.parse import urlencode

from .services.mercadolivre.mercadolivre import buscar_produtos_mercadolivre
from .schemas import Produto

router = APIRouter()

CLIENT_ID = "2405638697930169"
CLIENT_SECRET = "deprecated"
REDIRECT_URI = "https://www.dermasync.com.br/callback"

@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"erro": "Código não encontrado"}

    token_url = "https://api.mercadolibre.com/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=urlencode(data))

    if response.status_code == 200:
        token_data = response.json()
        print("✅ Token obtido:", token_data)
        return {"sucesso": "Token recebido com sucesso", "token": token_data}
    else:
        print("❌ Erro ao obter token:", response.text)
        return {"erro": response.text}


@router.post("/sugestoes-produtos", response_model=list[Produto])
async def sugestoes_produtos(tags: list[str]):
    return await buscar_produtos_mercadolivre(tags)
