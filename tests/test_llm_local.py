import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import pytest
from app.llm.factory import get_llm_client


class TestLlmLocal:
    @pytest.fixture
    def llm_client(self):
        return get_llm_client()

    @pytest.fixture
    def sample_text(self):
        return '''
        Queridos, tudo bom?

        Que tempinho mais ressecado é esse, não??

        Aqui em Cuiabá ( Cuiabrasa para os íntimos!), pelo menos, estamos com 30% de umidade e a minha pele tem gritado  heeeellllpppp de tão ressecada.

        O problema da pele xerótica ( ressecada) é que apresenta uma possibilidade maior de desenvolver atopias (alergias), pruridos ( coceiras) e ceratose pilar ( aquelas bolinhas ásperas na face lateral dos braços e pernas). Sem contar no aspecto craquelê horroroso que dá vontade de cobrir com burca o corpo inteiro!!

        Pensando em uma pele corporal mais lisinha, criei um hidratante caseiro turbinadíssimo, com todas as propriedades que eu, enquanto dermatologista, considero essencial na hora de  fazer uma boa hidratação em casa .

        Esses dois  ( Cetaphil Loção hidratante 473 ml ou Lipikar Loção 400 ml) são os meus preferidos. 

        Primeiro porque não tem cheiro.
        Segundo porque entram na categoria de hidratante "medicamento ", um produto destinado para tratar a pele ressecada.
        Terceiro que a textura deles é bem leve. ( detesto coisa pegajosa!)

        Para enriquecer a formulação, escolhi:

         50 ml do Bepantol solução, vitamina B5  ( quem disse que ele só serve para os cabelos??)
        50 ml de Óleo de semente de uva para diminuir a perda de água para o meio externo e repor antioxidantes para a pele ( rejuvenescedor)
        40 ml ( 1 frasco) do Cicaplast para aumentar a regeneração e recompor a barreira cutânea.

        Misture tudo ( voccê vai ter aproximadamente 550 ml de hidratante ) e mantenha em um frasco pump profissional de 600 ml ou mais  que você encontra em loja de salão de beleza e aplique  na pele corporal do pescoço aos pés, úmida 1x ao dia, pela noite, ou 2x ao dia.

        Essa misturinha dura em torno de 4 meses e vale muiiito a pena o investimento!

        A pele se mantém hidratada e lisinha por muito mais tempo...!

        Um beijão, amorecos, nos vemos logo!
        '''

    def test_extrair_idade_e_genero(self, llm_client, sample_text):
        prompt = (
            "A partir do texto abaixo, extraia a idade e o gênero do usuário. "
            "Retorne um JSON com os campos 'idade' e 'genero'. "
            "Se a informação não estiver presente, retorne null para os campos.\n\n"
            f"TEXTO:\n{sample_text}"
        )
        resposta = llm_client.completar(prompt)
        try:
            dados = json.loads(resposta)
        except json.JSONDecodeError:
            pytest.fail(f"Resposta do LLM não é um JSON válido: {resposta}")

        assert isinstance(dados, dict)
        assert "idade" in dados
        assert "genero" in dados

    def test_extrair_tags(self, llm_client, sample_text):
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
            f"TEXTO:\n{sample_text}"
        )
        resposta = llm_client.completar(prompt)
        try:
            dados = json.loads(resposta)
        except json.JSONDecodeError:
            pytest.fail(f"Resposta do LLM não é um JSON válido: {resposta}")

        assert isinstance(dados, dict)
        assert "sintomas" in dados
        assert "produtos_naturais" in dados
        assert "terapias_realizadas" in dados
        assert "medicamentos" in dados
