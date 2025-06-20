import pytest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from app.pipeline.B_enriquecimento.enriquecer_metadados import processar_relato  # adapte para seu import real
import logging
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# Teste para ler um arquivo JSONL bruto e enriquecer os metadados
# O teste deve garantir que o arquivo JSONL enriquecido tenha o formato correto e os campos obrigatórios estejam presentes.
relato_real=  {"id_relato": "5ab7a3b6132f409aacd90a3097ad4ceb", "origem": {"plataforma": "facebook", "link": None, "tipo": "comentario", "ano_postagem": None, "grupo": "Dermatite Atópica Brasil", "ctx_id": "1234567890"}, "versao_pipeline": "v0.0.1", "data_modificacao": "2025-06-10T07:58:35.656562", "conteudo_original": "Queridos, tudo bom?\nra os Cetaphil Loção hidratante 473 ml ou Lipikar Loção 400 ml) são os meus preferidos. \n\nPrimeiro porque não tem cheiro.\nSegundoleve. ( detesto coisa pegajosa!)\n\nPara enriquecer a formulação, escolhi:\n\n 50 ml do Bepantol solução, vitamina B5  ( quem disse que ele só serve para os cabelos??)\n50 ml de Óleo de semente de uva para diminuir a perda de água para o meio externo e repor antioxidantes para a pele ( rejuvenescedor)\n40 ml ( 1 frasco) do Cicaplast para aumentar a regeneração e recompor a barreira cutânea.\n\nMisture tudo ( voccê vai ter aproximadamente 550 ml de hidratante ) e mantenha em um frasco pump profissional de 600 ml ou mais  que você encontra em loja de salão de beleza e aplique  na pele corporal do pescoço aos pé"}



@pytest.mark.asyncio
async def test_enriquecer_metadados_formato_valido():
    # === Mock de um relato bruto ===
    relato_bruto = {
        "id_relato": "abc123def456ghi789xyz",
        "origem": "facebook",
        "data_modificacao": datetime.utcnow().isoformat(),
        "conteudo_original": "Olá meus amores. Tenho dermatite atópica nas pernas e usei cetirizina por 3 dias e vaselina por mais 7 dias. Melhorei bastante, mas ainda sinto coceira ocasional.",
        "versao_pipeline": "v0.0.1",
        "origem": {
            "plataforma": "facebook",
            "link": "https://facebook.com/groups/dermatite/posts/123456789",
            "tipo": "comentario",
            "data_postagem": None,
            "grupo": "Dermatite Atópica Brasil",
            "usuario_aparente": None
        }
    }

    # === Processa ===
    enriquecido = processar_relato(relato_real)
    logger.debug("Relato enriquecido: %s", enriquecido)
    # === Valida campos obrigatórios ===
    assert "idade" in enriquecido
    assert "genero" in enriquecido
    assert "classificacao_etaria" in enriquecido
    assert "llm_processamento" in enriquecido
    assert "status_llm" in enriquecido
    assert enriquecido["status_llm"] in ["concluido", "erro"]

    # === Validação contra o schema oficial ===
    schema_path = Path("./app/schema/relato_schema.json")
    assert schema_path.exists(), "Arquivo de schema JSON não encontrado."

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=enriquecido, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Erro de schema: {e.message}")


@pytest.mark.asyncio
async def test_if_jsonl_linha_valido():
    schema_path = Path("./app/schema/relato_schema.json")
    with open(schema_path, "r") as f:
        schema = json.load(f)
    linha = {"id_relato": "5ab7a3b6132f409aacd90a3097ad4ceb", "origem": {"plataforma": "facebook", "link": None, "tipo": "comentario", "ano_postagem": None, "grupo": "Dermatite Atópica Brasil", "ctx_id": "1234567890"}, "versao_pipeline": "v0.0.1", "data_modificacao": "2025-06-10T07:58:35.656562", "conteudo_original": "Queridos, tudo bom?\n\nQue tempinho mais ressecado é esse, não??\n\nAqui em Cuiabá ( Cuiabrasa para os íntimos!), pelo menos, estamos com 30% de umidade e a minha pele tem gritado  heeeellllpppp de tão ressecada.\n\nO problema da pele xerótica ( ressecada) é que apresenta uma possibilidade maior de desenvolver atopias (alergias), pruridos ( coceiras) e ceratose pilar ( aquelas bolinhas ásperas na face lateral dos braços e pernas). Sem contar no aspecto craquelê horroroso que dá vontade de cobrir com burca o corpo inteiro!!\n\nPensando em uma pele corporal mais lisinha, criei um hidratante caseiro turbinadíssimo, com todas as propriedades que eu, enquanto dermatologista, considero essencial na hora de  fazer uma boa hidratação em casa .\n\nEsses dois  ( Cetaphil Loção hidratante 473 ml ou Lipikar Loção 400 ml) são os meus preferidos. \n\nPrimeiro porque não tem cheiro.\nSegundo porque entram na categoria de hidratante \"medicamento \", um produto destinado para tratar a pele ressecada.\nTerceiro que a textura deles é bem leve. ( detesto coisa pegajosa!)\n\nPara enriquecer a formulação, escolhi:\n\n 50 ml do Bepantol solução, vitamina B5  ( quem disse que ele só serve para os cabelos??)\n50 ml de Óleo de semente de uva para diminuir a perda de água para o meio externo e repor antioxidantes para a pele ( rejuvenescedor)\n40 ml ( 1 frasco) do Cicaplast para aumentar a regeneração e recompor a barreira cutânea.\n\nMisture tudo ( voccê vai ter aproximadamente 550 ml de hidratante ) e mantenha em um frasco pump profissional de 600 ml ou mais  que você encontra em loja de salão de beleza e aplique  na pele corporal do pescoço aos pés, úmida 1x ao dia, pela noite, ou 2x ao dia.\n\nEssa misturinha dura em torno de 4 meses e vale muiiito a pena o investimento!\n\nA pele se mantém hidratada e lisinha por muito mais tempo...!\n\nUm beijão, amorecos, nos vemos logo!", "idade": 22, "genero": "Feminino", "classificacao_etaria": "Adulto", "sintomas": ["pele ressecada", "atopias (alergias)", "pruridos (coceiras)", "ceratose pilar", "aspecto craquelê"], "produtos_naturais": ["Óleo de semente de uva"], "terapias_realizadas": [], "medicamentos": [{"nome_comercial": "Cetaphil Loção hidratante", "frequencia": "ausente", "duracao": "ausente"}, {"nome_comercial": "Lipikar Loção", "frequencia": "ausente", "duracao": "ausente"}, {"nome_comercial": "Bepantol solução", "frequencia": "ausente", "duracao": "ausente"}, {"nome_comercial": "Cicaplast", "frequencia": "1x ao dia, pela noite, ou 2x ao dia", "duracao": "4 meses"}], "conteudo_anonimizado": "conteuddo anonimizado", "llm_processamento": {"inicio": "2025-06-20T14:21:07.610044", "fim": "2025-06-20T14:21:09.652177", "duracao_ms": 2042, "tentativas": 1, "erro": None, "modelo": "gemini-2.0-flash"}, "status_llm": "concluido"}
    assert isinstance(linha, dict), "A linha deve ser um objeto JSON."
    validate(instance=linha, schema=schema)