import json
from typing import List, Literal, Optional

# Nenhuma mudança aqui
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- ESTRUTURA Pydantic (sem alterações) ---
class Intervencao(BaseModel):
    ordem_temporal: int = Field(description="Ordem que a intervenção aparece no texto")
    nome_comercial: Optional[str] = Field(description="Nome comercial do produto")
    principio_ativo: Optional[str] = Field(description="Princípio ativo do medicamento, se conhecido")
    escala_eficacia: Optional[Literal["Melhora total", "Melhora significativa", "Melhora parcial", "Sem efeito", "Piora"]] = Field(description="Eficácia percebida pelo paciente")
    comentario_extraido: Optional[str] = Field(description="Comentário literal do paciente sobre a intervenção")
    trecho_referente: str = Field(description="Trecho exato do texto que comprova os dados")

class AnaliseRelato(BaseModel):
    raciocinio: str = Field(description="Raciocínio passo a passo sobre como o relato foi analisado para preencher os campos.")
    tags: List[str] = Field(description="Palavras-chave ou temas citados no relato")
    microdepoimento: str = Field(description="Uma frase útil e clara que resume a experiência do paciente")
    intervencoes: List[Intervencao]

# --- Função da Cadeia (com o prompt simplificado) ---
def criar_cadeia_analise_local(output_schema: BaseModel, nome_modelo_ollama: str= "poc-gemma-gaia"):
    parser = JsonOutputParser(pydantic_object=output_schema)

    # --- CORREÇÃO PRINCIPAL: Prompt muito mais simples ---
    # Removemos a injeção do {formato_json} e descrevemos a saída de forma mais direta.
    prompt_template = """
    Você é um **{persona}** no contexto **{contexto}**. Sua tarefa é **{acao_necessaria}** sobre o relato a seguir, que está entre as tags <relato>.
    <relato>
    {conteudo}
    </relato>
    Com base nesse texto, gere um **JSON**, respondendo APENAS isso, com os seguintes campos, e 'null' quando não for possível:

        {{  
            "tags": ["palavras-chave ou temas citados no relato"],
            "microdepoimento": "uma frase útil e clara que resume a experiência do paciente",
            "tituloRelato": "um título curto e descritivo do relato, como 'Tratamento com pomada de calêndula'",
             "paciente":    {{
                                "idade_descrita": "...", # inferir do texto ou 'null'
                                "sexo_biologico": "...", # inferir do texto ou 'null'
                                "faixa_etaria_calculada": # bebê, crianca, adolescente, adulto, idoso ou 'null'
                            }},
            "quadro_clinico": 
                            {{
                                "sintomas_descritos": [...], # Lista de sintomas mencionados
                                "localizacao_lesoes": [...], # Partes do corpo afetadas
                                "severidade_percebida": .., # alta, baixa, media ou null
                                "gatilhos_mencionados": ["alimentação, ..."], # O que piora ou desencadeia as crises
                                "duracao_crise": ... # Se o texto mencionasse a duracao, ou null
                            }},
            "racionio": "...", # Raciocínio passo a passo sobre como o relato foi analisado para preencher os campos.				
            "intervencoes_medicamentos": [
                        {{
                        "nome_comercial": "...",
                        "principio_ativo": "...",
                        "forma_farmaceutica": "...",
                        "via_de_administracao": "...",
                        "tempo_uso": "...",
                        "frequencia_uso": "...",
                        "eficacia_percebida": "...", # Melhora, Piora, inconclusivo, null
                        "efeitos_colaterais": ["..."],
                        "comentario_extraido": "...",
                        "trecho_referente": "...",
                        "tipo_intervencao": "...",
                        "cid10_relacionado": [...], # CID10 da doença se possível ou []
                        "ordem_temporal": 0, # Ordem que a intervenção aparece no texto.ex: 1, 2,...
                        
                        }},
                        ...
                    ]
        }}
                
                Retorne somente um JSON puro. Não use ```json ou qualquer formatação de markdown.
            """
    # --- FIM DA CORREÇÃO PRINCIPAL ---
    # O ChatPromptTemplate não precisa mais de partial_variables, pois removemos {formato_json}
    print("🔍 Criando cadeia de análise com o modelo:", nome_modelo_ollama)
   

    prompt = ChatPromptTemplate.from_template(template=prompt_template)
    
    model = ChatOllama(
        model=nome_modelo_ollama,
        format="json",
        temperature=0.0
    )

    chain = prompt | model | parser
    return chain

# --- Execução (sem alterações) ---
meu_modelo_gemma = "llama-poc"

persona_arg = "ANALISTA DE DADOS CLÍNICOS especialista em extração de informações de textos não estruturados"
contexto_arg = "dermatologia e farmacovigilância popular" # Esta variável não é mais usada no novo prompt, mas mantemos por consistência
acao_necessaria_arg = "extrair informações estruturadas sobre tratamentos de dermatite atópica"
conteudo_arg = """
dermatite atópica grave antes e depois Desde pequena tenho isso, mas sempre falaram que era alergia tenho rinite. Passei quase 20 anos da minha vida com coceiras,feridas e desconforto. Essa semana recebi diagnóstico de escabiose sarna, tomei as medicações porém só piorou. Fui antes de ontem novamente ao hospital e o médico disse que ia m hipótese alguma era sarna, é dermatite atópica grave. Receitou prednisona, cefalexina e uma pomada de acetato de dexametasona. Ainda não tá tão melhor pois hoje é o segundo dia da medicação, porém a coceira já diminui drasticamente e agora está secando. Pra quem ficou 20 anos sofrendo sem saber exatamente o que era, ver as feridas melhorando é muito animador.
"""

cadeia_de_analise = criar_cadeia_analise_local(
    output_schema=AnaliseRelato,
    nome_modelo_ollama=meu_modelo_gemma
)

print("Invocando o modelo local via Ollama... Isso pode levar um momento.")

resultado = cadeia_de_analise.invoke({
    "persona": persona_arg,
    "contexto": contexto_arg,
    "acao_necessaria": acao_necessaria_arg,
    "conteudo": conteudo_arg
})

print("\n--- RESULTADO DA EXTRAÇÃO ---")
print(json.dumps(resultado, indent=2, ensure_ascii=False))