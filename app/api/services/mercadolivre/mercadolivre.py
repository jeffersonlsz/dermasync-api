import httpx
from ...schemas import Produto

""" # app mercadolivre
ID do aplicativo
2405638697930169
# chave mercadolivre
TtZvgdVjAeZ3DFQrSzX0BsEpD0zN0gIP """

BASE_URL = "https://api.mercadolibre.com/sites/MLB/search"

async def buscar_produtos_mercadolivre(tags: list[str]) -> list[Produto]:
    resultados = []
    async with httpx.AsyncClient() as client:
        for tag in tags:
            resp = await client.get(BASE_URL, params={"q": tag})
            data = resp.json()
            for item in data.get("results", [])[:3]:  # Pega os 3 primeiros por tag
                resultados.append(Produto(
                    titulo=item["title"],
                    preco=item["price"],
                    link=item["permalink"],
                    thumbnail=item["thumbnail"],
                    origem="mercadolivre"
                ))
    print(resultados)
    return resultados
