import tomllib
import pandas as pd

from modules.ai_analysis import generate_ai_analysis


# Carrega a chave da API
with open(".streamlit/secrets.toml", "rb") as file:
    secrets = tomllib.load(file)


# Cria um conjunto de insights fictícios
insights = pd.DataFrame([
    {
        "Tipo": "Contextual",
        "Indicador": "Materiais abaixo do estoque mínimo",
        "Agregação": "Contagem",
        "Insight": "10 de 60 materiais estão abaixo do estoque mínimo.",
        "Evidência": "16,7% dos materiais.",
        "Atenção": "Avaliar necessidade de reposição."
    },
    {
        "Tipo": "Contextual",
        "Indicador": "Necessidade de reposição",
        "Agregação": "Soma",
        "Insight": "São necessárias 188 unidades para atingir o estoque mínimo.",
        "Evidência": "188 unidades.",
        "Atenção": "Validar quantidades e disponibilidade."
    },
    {
        "Tipo": "Contextual",
        "Indicador": "Valor estimado de reposição",
        "Agregação": "Soma",
        "Insight": "O valor estimado para reposição é de R$ 50.565,28.",
        "Evidência": "R$ 50.565,28.",
        "Atenção": "Estimativa sujeita à validação dos preços."
    }
])


# Executa a análise com IA
print("\nGERANDO ANÁLISE COM GEMINI...\n")

analysis = generate_ai_analysis(
    insights=insights,
    api_key=secrets["GEMINI_API_KEY"]
)

print("\nRESULTADO DA ANÁLISE:\n")
print(analysis)