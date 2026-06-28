from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json
import logging
import re

logger = logging.getLogger(__name__)

def remove_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def fix_common_json_issues(text: str) -> str:
    # corrige strings consecutivas sem vírgula
    text = re.sub(r'"\s*\n\s*"', '", "', text)

    # remove trailing commas
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)

    return text

def extract_json_block(text: str) -> str:

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("Nenhum JSON encontrado na resposta do LLM")

    return match.group(0)

class Metadata(BaseModel):
    idade: Optional[int]
    genero: Optional[str]
    sintomas: List[str] = Field(default_factory=list)
    tratamentos_mencionados: List[str] = Field(default_factory=list)
    regioes_afetadas: List[str] = Field(default_factory=list)
    temporal_markers: List[str] = Field(default_factory=list)
    titulo_resumido: Optional[str] = None
    solucao_encontrada: Optional[str] = None
    faixa_etaria: Optional[str] = None
    resumo_publico: Optional[str] = None
    
    # para validar a idade e não falhar em casos como '4 meses'
    @field_validator("idade", mode="before")
    @classmethod
    def validar_idade(cls, v):
        if v is None:
            return None

        try:
            return int(v)
        except Exception:
            return None

class LLMOutputParser:

    def __init__(self, llm_client):
        self.llm = llm_client

    def parse_metadata(self, response: str) -> Metadata:
        try:
            return self._parse(response)

        except Exception as e:
            logger.warning("[parser] primeira tentativa falhou: %s", e)

            repaired = self._repair_with_llm(response)

            return self._parse(repaired)
    
    def parse_anonymous_content(self, response: str) -> str:
        # remove ANSI codes
        cleaned = remove_ansi(response)

        # extrai o bloco JSON
        cleaned = extract_json_block(cleaned)

        # corrige problemas comuns de JSON
        cleaned = fix_common_json_issues(cleaned)

        logger.debug("[parser] cleaned json: %s", cleaned)

        data = json.loads(cleaned)

        return data
    
    def _parse(self, response: str) -> Metadata:
        cleaned = remove_ansi(response)
        cleaned = extract_json_block(cleaned)
        cleaned = fix_common_json_issues(cleaned)

        logger.debug("[parser] cleaned json: %s", cleaned)

        data = json.loads(cleaned)

        return Metadata(**data)

    def _repair_with_llm(self, bad_response: str) -> str:
        prompt = f"""
                    Corrija o JSON abaixo.

                    Regras:
                    - Retorne apenas JSON válido
                    - Não adicione explicações
                    - Não altere o conteúdo semântico

                    JSON:
                    {bad_response}
                    """
        return self.llm.generate(prompt)
