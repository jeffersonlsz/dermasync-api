# app/api/endpoints.py
"""
Rotas principais da API pública do projeto DermaSync.
Inclui endpoints para envio de relatos, verificação de status e extração de insights.
"""

import datetime
import json
import time
from pprint import pprint  # Moved to top-level imports
from typing import Literal  # Removed since it's unused

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    QueryInput,
)  # Kept despite being unused (might be needed for type hints)
from app.api.schemas import (  # Changed from relative to absolute import
    BuscarPorTagsRequest,
    JornadaPayload,
    QueryRequest,
    RequisicaoRelato,
    SolucaoRequest,
    TextoTags,
)
from app.chroma.buscador_segmentos import _buscar_por_tags, buscar_segmentos_similares
from app.chroma.buscador_tags import contar_tags
from app.firestore.client import db  # Changed from relative to absolute import
from app.llm.gemini import model

router = APIRouter()

# Caminho fixo do arquivo .jsonl
ARQUIVO_RELATOS = (
    "app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-20250529.jsonl"
)


@router.post("/buscar-relato-completo")
def buscar_relato_completo(payload: RequisicaoRelato):
    try:
        with open(ARQUIVO_RELATOS, "r", encoding="utf-8") as f:
            for linha in f:
                registro = json.loads(linha.strip())
                if registro.get("id_relato") == payload.id_relato:
                    return {
                        "id_relato": registro["id_relato"],
                        "conteudo": registro["conteudo_anon"],
                    }
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500, detail="Arquivo de relatos não encontrado."
        ) from exc
    raise HTTPException(status_code=404, detail="Relato não encontrado.")


@router.post("/obter-tags-populares")
def obter_tags_populares():
    populares = contar_tags()
    if not populares:
        raise HTTPException(status_code=404, detail="Nenhuma tag popular encontrada.")
    json_return = {}
    for tag, freq in populares:
        tag_formatada = tag.replace("tag_", "").replace("_", " ").title()
        json_tag = {"tag": tag_formatada, "frequencia": freq}
        json_return[tag_formatada] = json_tag
    return {"tags_populares": json_return}


@router.post("/buscar-por-tags")
def buscar_por_tags(req: BuscarPorTagsRequest):
    print(
        f"🔍 Buscando por tags: {req.tags}, modo: {req.modo}, k: {req.k}, log: {req.log}"
    )

    resultados = _buscar_por_tags(tags=req.tags, modo=req.modo, k=req.k, log=req.log)
    if not resultados:
        raise HTTPException(
            status_code=404,
            detail="Algo deu errado ou não foram encontrados resultados.",
        )
    return {"resultados": resultados}


@router.post("/consultar-segmentos")
def consultar_segmentos(req: QueryRequest):
    resultados = buscar_segmentos_similares(req.texto, req.k)
    return {"resultados": resultados}


@router.post("/gerar-solucao")
async def gerar_solucao(req: SolucaoRequest):
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
        response = model.generate_content(prompt)
        return {"resposta": response.text}
    except Exception as e:
        return {"erro": str(e)}


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
        except json.JSONDecodeError:
            tags = []

        return {"tags": tags}
    except Exception as e:
        return {"erro": str(e), "tags": []}


@router.post("/processar-jornada")
async def processar_jornada(jornada: JornadaPayload):
    pprint(f" dados da jornada a ser processada {jornada}")
    doc_id = jornada.id
    ref = db.collection("jornadas").document(doc_id)

    try:
        ref.update(
            {
                "statusLLM": "processando",
                "llm_processamento.inicio": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Documento não encontrado: {e}"
        ) from e

    prompt = f"""
A seguir está o relato de um paciente com dermatite atópica.

Idade: {jornada.idade or 'não informada'}
Sexo: {jornada.sexo or 'não informado'}
Classificação: {jornada.classificacao or 'não informada'}
Descrição:
\"\"\"{jornada.descricao}\"\"\"
Com base nesse texto, gere um JSON com os seguintes campos:
{{  
  "tags": ["aqui são palavras-chave. Deve conter temas citados no relato como 'hidratação', 'pomada', 'corticoide', 'alimentação', 'banho morno', 'canabidiol', 'dieta vegana'. Não precisa ser exaustivo, mas deve conter as palavras mais relevantes citadas no relato."],
  "microdepoimento": "uma frase útil e clara que resume a experiência do paciente",
  "tituloRelato": "título curto que resume o relato, como 'Tratamento com pomada de calêndula'. Bem direto ao ponto.",
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
  ],
  terapias_realizadas: ["aqui são as terapias realizadas, como autohemoterapia, ozonioterapia etc"],
  produtos_naturais: ["aqui são os produtos naturais mencionados, como óleos essenciais, fitoterápicos etc"]

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
        print("|" + response.text[:100] + "|")
        raw = response.text.strip()

        if raw.startswith("```json"):
            raw = raw.removeprefix("```json").removesuffix("```").strip()
        elif raw.startswith("```"):
            raw = raw.removeprefix("```").removesuffix("```").strip()
        print("🔎 RESPOSTA POLIDA DO GEMINI:")
        print("|" + response.text[:150] + "|")
        data = json.loads(raw)
        print(f"🔎 DADOS EXTRAÍDOS DO GEMINI: {data}")

        current_tentativas = ref.get().to_dict().get("tentativas_llm", 0)
        print(f"🔄 Tentativas LLM atuais: {current_tentativas}")

        ref.update(
            {
                "tituloRelato": data.get("tituloRelato", "--"),
                "tags_extraidas": data.get("tags", []),
                "microdepoimento": data.get("microdepoimento", ""),
                "relatoProcessado": data.get("relatoProcessado", ""),
                "intervencoes_mencionadas": data.get("intervencoes", []),
                "terapias_realizadas": data.get("terapias_realizadas", []),
                "produtos_naturais": data.get("produtos_naturais", []),
                "statusLLM": "concluido",
                "llm_processamento.fim": datetime.datetime.utcnow().isoformat(),
                "llm_processamento.duracao_ms": int((fim - inicio) * 1000),
                "ultima_tentativa_llm": datetime.datetime.utcnow().isoformat(),
                "tentativas_llm": current_tentativas + 1,
            }
        )
        print(f"✅ Processamento concluído para o documento {doc_id}.")
        return {"status": "ok", "id": doc_id, "duracao_ms": int((fim - inicio) * 1000)}
    except Exception as e:
        ref.update(
            {
                "statusLLM": "erro",
                "erro_llm": str(e),
                "ultima_tentativa_llm": datetime.datetime.utcnow().isoformat(),
            }
        )
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar LLM: {e}"
        ) from e
