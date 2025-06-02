from fastapi import APIRouter, HTTPException
from .schemas import JornadaPayload, TextoTags, SolucaoRequest, QueryInput, QueryRequest
from ..llm.gemini import model
from ..firestore.client import db, increment_function
import time
import json
import datetime
from app.chroma.ingest_from_jsonl import ingerir_jsonl
from app.chroma.buscar_segmentos_similares import buscar_segmentos_similares


router = APIRouter()

@router.post("/consultar-segmentos")
def consultar_segmentos(req: QueryRequest):
    resultados = buscar_segmentos_similares(req.texto, req.k)
    return {"resultados": resultados}


@router.post("/ingerir-relatos")
def iniciar_ingestao():
    caminho = "./app/dados/depoimentos_extraidos.jsonl"
    qtd = ingerir_jsonl(caminho)
    return {"status": "ok", "quantidade": qtd}

@router.get("/hello")
async def get_hello():
    return {"message": "hello world"}


# Endpoint que gera a solução baseada nos dados do paciente
@router.post("/gerar-solucao")
async def gerar_solucao(req: SolucaoRequest):
    # Monta o prompt
    prompt = f"""
    A seguir está o relato de um paciente com dermatite atópica, {req.idade} anos, {req.genero}, com sintomas em {req.localizacao}:

    "{req.sintomas}"

    Com base nesse relato, extraia apenas a solução que esse paciente encontrou para aliviar ou controlar os sintomas. 
    Descreva de forma objetiva e concisa o que foi feito, incluindo produtos usados, frequência, duração, mudanças de hábitos e outras ações práticas mencionadas.
    Se não houver nenhuma solução clara no relato, responda apenas: "O paciente não conseguiu encontrar solução para sua condição." Se for mulher, diga "A paciente...."

    Não precisa dizer que o paciente precisa ir ao médico, nem que a dermatite atópica não tem cura.
    Não precisa incluir informações adicionais, apenas a solução. A resposta deve ser curta e direta, sem rodeios.

    

    """

    try:
        # Chama a API Gemini
        response = model.generate_content(prompt)
        return { "resposta": response.text }

    except Exception as e:
        # Retorna erro amigável se algo falhar
        return { "erro": str(e) }


@router.post("/extrair-tags")
async def extrair_tags(req: TextoTags):
    prompt = f"""
    Abaixo está o texto de um relato de um paciente com dermatite atópica. Extraia apenas as palavras-chave úteis como tags, relacionadas a ações, produtos ou temas relevantes para tratamento. Responda com uma lista JSON de palavras simples, como:
    ["hidratação", "pomada", "corticoide", "alimentação", "banho morno"]

    Texto: "{req.descricao}"
    """

    try:
        response = model.generate_content(prompt)
        texto = response.text.strip()

        try:
            tags = json.loads(texto)
        except:
            tags = []

        return {"tags": tags}
    except Exception as e:
        return {"erro": str(e), "tags": []}

@router.post("/processar-jornada")
async def processar_jornada(jornada: JornadaPayload):
    doc_id = jornada.id
    ref = db.collection("jornadas").document(doc_id)

    try:
        ref.update({
            "statusLLM": "processando",
            "llm_processamento.inicio": datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Documento não encontrado: {e}")

    # 🧠 Prompt para o Gemini com {{ }} para escapar corretamente
    prompt = f"""
A seguir está o relato de um paciente com dermatite atópica.

Idade: {jornada.idade or 'não informada'}
Sexo: {jornada.sexo or 'não informado'}
Classificação: {jornada.classificacao or 'não informada'}

Descrição:
\"\"\"{jornada.descricao}\"\"\"

Com base nesse texto, gere um JSON com os seguintes campos:

{{  
  "tags": ["palavras-chave ou temas citados no relato"],
  "microdepoimento": "uma frase útil e clara que resume a experiência do paciente",
  "tituloRelato": "um título curto e descritivo do relato, como 'Tratamento com pomada de calêndula'",
  "intervencoes": [
    {{
      "nome_comercial": "...",
      "principio_ativo": "...",
      "forma_farmaceutica": "...",
      "via_de_administracao": "...",
      "tempo_uso": "...",
      "frequencia_uso": "...",
      "eficacia_percebida": "...",
      "efeitos_colaterais": ["..."],
      "comentario_extraido": "...",
      "trecho_referente": "...",
      "tipo_intervencao": "...",
      "cid10_relacionado": ["L20.0"],
      "nivel_evidencia": "...",
      "origem": "mencionado pelo usuário"
    }}
  ]
}}

Não invente dados. Se algo não estiver claro, use null.
Retorne somente um JSON puro. Não use ```json ou qualquer formatação de markdown.
"""

    try:
        inicio = time.time()
        response = model.generate_content(prompt)
        fim = time.time()

        raw = response.text
        print("🔎 RESPOSTA BRUTA DO GEMINI:")
        print("|"+response.text+"|")
        raw = response.text.strip()

        # Remove bordas de Markdown tipo ```json ... ```
        if raw.startswith("```json"):
            raw = raw.removeprefix("```json").removesuffix("```").strip()
        elif raw.startswith("```"):
            raw = raw.removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        ref.update({
            "tags_extraidas": data.get("tags", []),
            "microdepoimento": data.get("microdepoimento", ""),
            "intervencoes_mencionadas": data.get("intervencoes", []),
            "statusLLM": "concluido",
            "llm_processamento.fim": datetime.datetime.utcnow().isoformat(),
            "llm_processamento.duracao_ms": int((fim - inicio) * 1000),
            "ultima_tentativa_llm": datetime.datetime.utcnow().isoformat(),
            "tentativas_llm": increment_function.Increment(1)
        })

        return {"status": "ok", "id": doc_id, "duracao_ms": int((fim - inicio) * 1000)}

    except Exception as e:
        ref.update({
            "statusLLM": "erro",
            "erro_llm": str(e),
            "ultima_tentativa_llm": datetime.datetime.utcnow().isoformat(),
            "tentativas_llm": increment_function.Increment(1)
        })
        raise HTTPException(status_code=500, detail=f"Erro ao processar LLM: {e}")
