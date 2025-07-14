# Orquestrador
# import json
import os
import json
import logging
import sys
import uuid
from datetime import datetime as datetime
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

from pydantic import BaseModel

print("Current Python path:", sys.path)
parent_dir = str(Path(__file__).resolve().parent.parent)
current_dir = str(os.curdir)
print("Before Python path :", sys.path)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
print("After Python path  :", sys.path)
from llm_client.base import get_llm_client
from app.schema.relato import RelatoCompleto
from app.utils.utils import log_location


# === CONFIGURAÇÕES ===
MODELO_LLM = "gemini-2.5-pro"  # Modelo LLM a ser usado llama-poc
DIRETORIO_JSONS_BRUTOS = Path("app/pipeline/dados/jsonl_brutos")
ENTRADA_JSONL_BRUTO = "relatos-20250620-facebook-v0.0.1.jsonl"
OUTPUT_DIR = Path("app/pipeline/dados/jsonl_enriquecidos")
JSONL_ENRIQUECIDO = "relatos-20251307-facebook-v0.0.1.enriquecido.jsonl"

logger = logging.getLogger(__name__)
 
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

def buscar_cliente_llm():
    client = get_llm_client("gemini", MODELO_LLM)
    logger.info(f"Usando cliente LLM: {client}")
    if not client:
        raise ValueError("Cliente LLM não configurado corretamente.")
    return client

# === MOCK DE FUNÇÕES DE EXTRAÇÃO ===
def extrair_idade_e_genero(conteudo: str) -> dict:
    # Substitua isso por chamada real ao LLM
    client = buscar_cliente_llm()
    prompt = (
        "A partir do texto abaixo, extraia a idade e o gênero do usuário. "
        "Retorne um JSON com os campos 'idade' e 'genero'.\n\n"
        f"TEXTO:\n{conteudo}"
    )
    logger.info(f"Enviando prompt para LLM: {prompt}...")
    resposta = client.completar(prompt)
    logger.info(f"Resposta do LLM: {resposta}")
    # Normalização da saída
    if resposta.startswith("```json"):
        resposta = resposta.removeprefix("```json").removesuffix("```").strip()
    elif resposta.startswith("```"):    
        resposta = resposta.removeprefix("```").removesuffix("```").strip()
    logger.info(f"Resposta sanitizada do LLM: {resposta}")
    try:    
        dados = json.loads(resposta)    
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise ValueError("Resposta do LLM não é um JSON válido.")
    if not isinstance(dados, dict):
        raise ValueError("Resposta do LLM deve ser um objeto JSON.")
    # Sanitização mínima
    return {
        "idade": dados.get("idade", None),
        "genero": dados.get("genero", None),
        "faixa_etaria_calculada": dados.get("faixa_etaria_calculada", None),
    }


def extrair_tags(conteudo: str) -> dict:
    """
    Extrai sintomas, produtos naturais, terapias realizadas e medicamentos.
    Retorna um dicionário com os campos já prontos para uso direto no JSON final.
    """
    client = buscar_cliente_llm()

    prompt = (
        "A partir do texto abaixo, extraia SOMENTE os seguintes dados como estrutura JSON:"
        "\n- sintomas\n- produtos_naturais\n- terapias_realizadas\n- medicamentos\n\n"
        "Formato de resposta (não inclua explicações):\n"
        "{\n"
        '  "sintomas": [...],\n'
        '  "produtos_naturais": [...],\n'
        '  "terapias_realizadas": [...],\n'
        '  "medicamentos": [\n'
        '    {"nome_comercial": ..., "frequencia": ..., "duracao": ... }\n'
        "  ]\n"
        "}\n\n"
        "Ignore nomes próprios e preencha com listas vazias ou 'ausente' se não houver informação.\n\n"
        f"TEXTO:\n{conteudo}"
    )
    logger.info(f"Enviando prompt para LLM: {prompt}...")
    resposta = client.completar(prompt)
    logger.info(f"Resposta do LLM: {resposta}")
    # Normalização da saída
    if resposta.startswith("```json"):
        resposta = resposta.removeprefix("```json").removesuffix("```").strip()
    elif resposta.startswith("```"):
        resposta = resposta.removeprefix("```").removesuffix("```").strip()
    logger.info(f"Resposta sanitizada do LLM: {resposta}")
    try:
        dados = json.loads(resposta)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise ValueError("Resposta do LLM não é um JSON válido.")

    if not isinstance(dados, dict):
        raise ValueError("Resposta do LLM deve ser um objeto JSON.")

    # Sanitização mínima
    return {
        "sintomas": dados.get("sintomas", []),
        "produtos_naturais": dados.get("produtos_naturais", []),
        "terapias_realizadas": dados.get("terapias_realizadas", []),
        "medicamentos": dados.get("medicamentos", []),
    }


def criar_cadeia_analisadora(output_schema: BaseModel, nome_modelo: str= "poc-gemma-gaia"):
    
    
    """
    Cria uma cadeia de análise com o modelo LLM especificado.
    """
    parser = JsonOutputParser(pydantic_object=output_schema)
    # Montar o prompt para a cadeia de análise
    # Gera os campos do JSON dinamicamente a partir do output_schema
    # import pdb; pdb.set_trace()
    campos={field: None for field in output_schema.model_fields.keys()}
    logger.info(f"{log_location()[40:]} CAMPOS GERADOS: " + str(campos) )
    prompt_template = """
    Você é um {persona} no contexto de {contexto}. Sua tarefa é {acao_necessaria} sobre o relato a seguir, que está entre as tags <relato>.
    <relato>
    {conteudo}
    </relato>
    Com base nesse texto, gere um **JSON**, respondendo APENAS isso, com os seguintes campos, e 'null' quando não for possível:

        {{
            {campos}
        }}
    Retorne somente um JSON puro. Não use ```json ou qualquer formatação de markdown.
    """
    logger.info(f"{log_location()[40:]}🔍 Criando cadeia de análise {output_schema.__name__} com o modelo: {nome_modelo}")
  
    logger.info(f"{log_location()[40:]} 🛶 Conteudo do template: {prompt_template}")
    
    prompt = ChatPromptTemplate.from_template(template=prompt_template, partial_variables={"campos": campos})
    
    logger.info(f"{log_location()[40:]} 📜 Renderizando prompt para depuração...")
    #new_var = 'ANALISTA DE DADOS CLÍNICOS'
    new_var={
       'persona':'ANALISTA DE DADOS CLÍNICOS',
       'contexto':['dermatologia e farmacovigilância popular'],
       'acao_necessaria':'extrair informações estruturadas sobre tratamentos de dermatite atópica conforme JSON especificado neste prompt',
       'conteudo':'Eu sou uma mulher de 30 anos e sofro de dermatite atópica desde a infância. Minha pele fica muito seca, com coceira intensa e vermelhidão, principalmente nas dobras dos braços e joelhos. Já usei diversas pomadas com corticoides, como a betametasona, que aliviava os sintomas, mas eles sempre voltavam. Recentemente, comecei a usar um creme hidratante à base de ureia e óleo de girassol, que tem ajudado a manter a pele mais hidratada. Também faço compressas com chá de camomila para acalmar a irritação. Evito banhos muito quentes e sabonetes perfumados. Às vezes, em crises mais fortes, tomo anti-histamínicos para controlar a coceira noturna. Tenho tentado identificar gatilhos alimentares, mas ainda não encontrei nada específico. Minha dermatologista sugeriu fototerapia, mas ainda não tive tempo de iniciar.'  
    }

    logger.info(f"{log_location()[40:]} 📜 Conteúdo do prompt: {prompt.format_prompt(**new_var)}")

    model = ChatOllama(
        model="poc-gemma-01",
        format="json",
        temperature=0.0
    )

    logger.info(f"{log_location()[40:]} ℹ️ Fim da cadeia de análise.")
    chain = prompt | model | parser
    return chain

# === ORQUESTRADOR ===
def processar_relato(dado: dict) -> dict:
    logger.info(f"Processando relato: {dado.get('id_relato', 'desconhecido')}")
    #logger.info(f"Conteúdo original: {dado.get('conteudo_original', 'vazio')}")
    
    # Extração de informações básicas
    inicio = datetime.now()
    erro = None
    tentativas = 1
    
    try:
        conteudo = dado.get("conteudo_original", "")
        if not conteudo:
            raise ValueError("Conteúdo original não pode ser vazio.")
        conteudo_anonimizado = criar_cadeia_analisadora(output_schema=RelatoCompleto, nome_modelo=MODELO_LLM).invoke(
            {   "conteudo": conteudo,
                "persona": "ANALISTA DE DADOS CLÍNICOS especialista em extração de informações de textos não estruturados",
                "contexto": "dermatologia e farmacovigilância popular",
                "acao_necessaria": "extrair informações estruturadas sobre tratamentos de dermatite atópica",
            }
        )["conteudo_tratado"]
        info_basica = extrair_idade_e_genero(conteudo)
        tags = extrair_tags(conteudo)
        logger.info(f"Extração de tags: {tags}")
        
    except Exception as e:
        logger.error(f"Erro ao processar relato: {e}")
        raise e
        #conteudo_anonimizado = f"Erro - não tratado: {conteudo}"
        #erro = str(e)
        #info_basica = {}
        #tags = {}

    fim = datetime.now()
    duracao_ms = int((fim - inicio).total_seconds() * 1000)

    enriquecido = {
        **dado,
        **info_basica,
        **tags,
        "conteudo_tratado": conteudo_anonimizado,
        "llm_processamento": {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_ms": duracao_ms,
            "tentativas": tentativas,
            "erro": erro,
            "modelo": MODELO_LLM,
        },
        "status_llm": "concluido" if not erro else "erro",
    }

    return enriquecido


# === EXECUÇÃO ===
def main():
    logger.info("ℹ️ Fase 02 - Início do processo de enriquecimento...")
    input_path = DIRETORIO_JSONS_BRUTOS / ENTRADA_JSONL_BRUTO
    output_path = OUTPUT_DIR / JSONL_ENRIQUECIDO
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"📤 Lendo de {input_path} e salvando enriquecidos em: {output_path}")

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for linha in fin:
            dado = json.loads(linha)
            enriquecido = processar_relato(dado)
            fout.write(json.dumps(enriquecido, ensure_ascii=False) + "\n")

    print("✅ Enriquecimento finalizado.")


if __name__ == "__main__":
    main()
