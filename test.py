
""" # app mercadolivre
ID do aplicativo
2405638697930169
# chave mercadolivre
TtZvgdVjAeZ3DFQrSzX0BsEpD0zN0gIP 

# Correct command syntax for Windows:
curl -X GET -H "Authorization: Bearer TtZvgdVjAeZ3DFQrSzX0BsEpD0zN0gIP" https://api.mercadolibre.com/applications/2405638697930169

"""
import httpx
import asyncio
import time
import os
import json
from urllib.parse import urlencode

""" https://auth.mercadolivre.com.br/authorization?response_type=code&client_id=2405638697930169&redirect_uri=https://www.dermasync.com.br/callback """

# ------------------ CONFIGURAÇÕES ------------------ #
CLIENT_ID = "2405638697930169"
CLIENT_SECRET = "TtZvgdVjAeZ3DFQrSzX0BsEpD0zN0gIP"
CODE = "TG-6850077009f70800015215ca-81588372"  # obtido via redirecionamento OAuth
TOKEN_FILE = "tokens.json"
REDIRECT_URI = "https://www.dermasync.com.br/callback" # tem que estar cadastrado no ML
ACCESS_TOKEN = "APP_USR-2405638697930169-061608-2cc348df13a8dea06c2c0c5459485a19-81588372"
USER_ID = "81588372"
# ------------------ TOKENS ------------------ #

async def inspecionar_conta():
    url = f"https://api.mercadolibre.com/users/{USER_ID}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

        print("📦 Status:", resp.status_code)
        if resp.status_code == 200:
            dados = resp.json()
            print("🔍 Resultado:")
            print("Tags:", dados.get("tags"))
            print("Permissões de venda:", dados.get("status", {}).get("sell"))
            print("Status site:", dados.get("status", {}).get("site_status"))
            print("Tipo de conta:", dados.get("user_type"))
        else:
            print("❌ Erro:", resp.text)

async def inspecionar_aplicacao():
    url = f"https://api.mercadolibre.com/applications/{CLIENT_ID}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

    print("📦 Status:", resp.status_code)
    print(resp.json())

def carregar_tokens():
    if os.path.exists(TOKEN_FILE):
        print(f"O arquivo {TOKEN_FILE} existe")
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_tokens(token_data):
    token_data["expires_at"] = int(time.time()) + token_data.get("expires_in", 21600)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

def token_expirado(token_data):
    return int(time.time()) >= token_data.get("expires_at", 0)

async def renovar_token(refresh_token):
    url = "https://api.mercadolibre.com/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, data=urlencode(data))
        if resp.status_code == 200:
            print("🔁 Token renovado com sucesso")
            token_data = resp.json()
            salvar_tokens(token_data)
            return token_data
        else:
            print("❌ Erro ao renovar token:", resp.text)
            return None
        
async def obter_token_valido():
    token_data = carregar_tokens()
    if not token_data:
        raise Exception("⚠️ Nenhum token salvo. Faça login e salve o token primeiro.")

    if token_expirado(token_data):
        print("⏳ Token expirado. Renovando...")
        token_data = await renovar_token(token_data["refresh_token"])

    return token_data

# ------------------ BUSCA DE PRODUTOS ------------------ #
async def buscar_recomendacoes_produtos_tags(tags: list[str]):
    token_data = await obter_token_valido()
    print(f"token valido obtido {token_data['access_token']}")
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    resultados = []

    async with httpx.AsyncClient() as client:
        for tag in tags:
            url = "https://api.mercadolibre.com/sites/MLB/search"
            params = {"q": tag}
            print(f"🔍 Buscando produtos para tag: {tag}")
            resp = await client.get(url, params=params, headers=headers)

            print("📦 Status:", resp.status_code)

            if resp.status_code == 200:
                dados = resp.json()
                for item in dados.get("results", [])[:3]:
                    resultados.append({
                        "tag": tag,
                        "titulo": item["title"],
                        "preco": item["price"],
                        "link": item["permalink"],
                        "thumbnail": item["thumbnail"]
                    })
            else:
                print(resp.request.url)
                print(resp.request.headers)

                print(f"❌ Erro ao buscar produtos para tag '{tag}': {resp.json()}")

    return resultados


async def buscar_usuario_logado():
    url = "https://api.mercadolibre.com/users/me"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

    print("📦 Status:", resp.status_code)
    print("👤 Dados do usuário:")
    print(resp.json())

async def buscar_produto_publico():
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {"q": "hidratante"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    print("📦 Status:", resp.status_code)
    print("🔍 Resultados:")
    print(resp.json())


async def teste_equivalente_curl():
    url = "https://api.mercadolibre.com/oauth/token"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": CODE,
        "redirect_uri": REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=urlencode(data))

        print("🔁 Requisição enviada ao Mercado Livre")
        print("📦 Status:", response.status_code)

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Token recebido:")
            print(token_data)
        else:
            print("❌ Erro:")
            print(response.text)

async def teste_url_autenticacao():
    base_url = "https://auth.mercadolivre.com.br/authorization"
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI
    }

    url_final = f"{base_url}?{urlencode(params)}"
    print("🔗 URL de autenticação Mercado Livre:")
    print(url_final)


async def obter_access_token():
    url = "https://api.mercadolibre.com/oauth/token"

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": CODE,
        "redirect_uri": REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=urlencode(data), headers=headers)

        if response.status_code == 200:
            print("✅ Sucesso ao obter token:")
            print(response.json())
        else:
            print(f"❌ Erro {response.status_code}")
            print(response.text)


async def buscar_status_usuario(user_id):
    url = f"https://api.mercadolibre.com/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    params = {
        "attributes": "status"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    print("📦 Status:", response.status_code)
    if response.status_code == 200:
        print("✅ Dados do status do usuário:")
        print(response.json())
    else:
        print("❌ Erro ao buscar status do usuário:")
        print(response.text)

if __name__ == "__main__":
    #asyncio.run(obter_access_token())
    #asyncio.run(inspecionar_conta()) 
    asyncio.run(inspecionar_aplicacao())

   #tags = ["hidratante", "corticóide", "creme sem perfume"]
   # resultados = asyncio.run(buscar_recomendacoes_produtos_tags(tags))
   # print("\n🔍 RESULTADOS:")
   # for r in resultados:
   #     print(f"- [{r['tag']}] {r['titulo']} - R${r['preco']} → {r['link']}")   
    
