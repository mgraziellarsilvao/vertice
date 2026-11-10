import json
import pandas as pd
from google import genai


MODEL_NAME = "gemini-3.5-flash-lite"


def prepare_insights(insights):
    """
    Prepara somente os insights calculados pelo Python.
    """

    if insights is None or insights.empty:
        return []

    relevant_columns = [
        "Tipo",
        "Indicador",
        "Agregação",
        "Insight",
        "Evidência",
        "Atenção"
    ]

    available_columns = [
        column
        for column in relevant_columns
        if column in insights.columns
    ]

    prepared = insights[available_columns].copy()
    prepared = prepared.fillna("Não informado")

    return prepared.to_dict(orient="records")


def generate_ai_analysis(insights, api_key):
    """
    Gera uma interpretação executiva com o Gemini.
    """

    if not api_key:
        raise ValueError("Chave da API Gemini não configurada.")

    prepared_insights = prepare_insights(insights)

    if not prepared_insights:
        return "Não existem insights suficientes para realizar a análise."

    client = genai.Client(api_key=api_key)

    data = json.dumps(
        prepared_insights,
        ensure_ascii=False,
        indent=2,
        default=str
    )

    prompt = f"""
Você é um analista sênior especializado em dados,
operações e inteligência de negócios.

Sua função é interpretar indicadores já calculados
por um sistema analítico e produzir uma análise executiva
precisa, objetiva e fundamentada.

DADOS DISPONÍVEIS:

{data}

REGRAS OBRIGATÓRIAS DE PRECISÃO:

1. Utilize exclusivamente os dados fornecidos.
2. Não invente números, indicadores, classificações ou acontecimentos.
3. Preserve integralmente os valores e percentuais apresentados.
4. Toda afirmação factual deve estar sustentada por um indicador
   ou evidência fornecida.
5. Não transforme uma situação potencial em um acontecimento confirmado.
6. Não confunda correlação com causalidade.
7. Não suponha consequências operacionais ou financeiras.
8. Não classifique itens como essenciais, críticos ou prioritários
   sem uma classificação explícita nos dados.
9. Não recomende compras, contratações ou ações imediatas
   sem evidências suficientes.
10. Quando uma informação não estiver disponível, declare
    explicitamente que não pode ser confirmada.

RESTRIÇÕES DE LINGUAGEM:

Não utilize os termos abaixo como fatos sem evidências específicas:

- Ruptura de estoque.
- Desabastecimento.
- Paralisação operacional.
- Prejuízo financeiro.
- Perda de vendas.
- Itens essenciais.
- Itens críticos.
- Risco iminente.

Exemplo de interpretação correta:

Dado: 10 materiais estão abaixo do estoque mínimo.

Correto:
"Dez materiais estão abaixo dos respectivos níveis mínimos,
representando 16,7% dos materiais analisados."

Incorreto:
"Dez materiais estão em ruptura e podem paralisar a operação."

DIFERENCIAÇÃO DAS INFORMAÇÕES:

- FATO: informação diretamente comprovada pelos indicadores.
- RISCO POTENCIAL: consequência possível que depende de validação.
- HIPÓTESE: explicação que não pode ser confirmada pelos dados.
- LIMITAÇÃO: informação necessária que não está disponível.

ESTRUTURA DA RESPOSTA:

## 1. Interpretação executiva
Apresente uma síntese objetiva da situação identificada.
Utilize somente conclusões sustentadas pelos indicadores.

## 2. Principais descobertas
Destaque os indicadores mais relevantes e seus valores.
Não repita informações desnecessariamente.

## 3. Pontos que merecem investigação
Apresente riscos potenciais e hipóteses.
Explique quais informações precisam ser verificadas.

## 4. Recomendações
Sugira ações proporcionais às evidências disponíveis.
Priorize validações e análises complementares quando necessário.

## 5. Limitações da análise
Informe quais conclusões não podem ser obtidas
com os dados disponíveis.

ESTILO:

- Português brasileiro.
- Linguagem executiva e profissional.
- Clareza e objetividade.
- Sem alarmismo.
- Sem conclusões especulativas.
- Sem repetição de indicadores.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError("O Gemini não retornou conteúdo.")

    return response.text