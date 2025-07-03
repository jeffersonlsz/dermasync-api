from collections import Counter

from app.chroma.factory import db_factory as factory

collection = factory.collection


def contar_tags():
    dados = collection.get(include=["metadatas"])
    contagem = Counter()

    for metadado in dados["metadatas"]:
        for chave, valor in metadado.items():
            if chave.startswith("tag_") and valor is True:
                contagem[chave] += 1

    return contagem.most_common(30)


def obter_tags_populares(top_n=10):
    ranking = contar_tags()
    return [
        tag.replace("tag_", "").replace("_", " ").title() for tag, _ in ranking[:top_n]
    ]


if __name__ == "__main__":
    # Teste rápido da função

    populares = contar_tags()
    for tag, count in populares:
        ttag = tag.replace("tag_", "").replace("_", " ").title()
        print(f"{ttag}: {count}")

    # Exemplo de uso
    # tags_populares = contar_tags(collection)
    # print(tags_populares)  # Exibe as tags mais populares e suas contagens
