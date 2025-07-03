from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.log_requests import LogRequestMiddleware

app = FastAPI()
app.add_middleware(LogRequestMiddleware)


from app.routes import imagens, relatos

app = FastAPI(title="DermaSync API - Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique ["https://www.seusite.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Incluindo o roteador da API
# app.include_router(api_router)


app.include_router(imagens.router)
app.include_router(relatos.router)


@app.get("/")
def home():
    return {"mensagem": "API online."}
