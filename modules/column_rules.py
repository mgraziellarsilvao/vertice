import re
import unicodedata


# Termos que identificam colunas de código/identificação.
# A comparação é feita por palavra inteira (separada por _, espaço, hífen etc.),
# e não por trecho de texto. Assim "id_cliente" e "codigo_produto" são
# identificadores, mas "quantidade", "unidades", "valor_liquido" e
# "capacidade" continuam sendo tratadas como colunas numéricas.

IDENTIFIER_WORDS = {"id", "codigo", "cod", "cpf", "cnpj", "cep", "telefone"}


def is_identifier_column(column_name):

    name = unicodedata.normalize(
        "NFKD",
        str(column_name).lower().strip()
    )

    name = "".join(
        char for char in name
        if not unicodedata.combining(char)
    )

    words = [
        word
        for word in re.split(r"[^a-z0-9]+", name)
        if word
    ]

    if any(
        word in IDENTIFIER_WORDS or word.startswith("codigo")
        for word in words
    ):
        return True

    # "numero_pedido", "numero_ordem"
    for current, following in zip(words, words[1:]):
        if current == "numero" and following in {"pedido", "ordem"}:
            return True

    return False
