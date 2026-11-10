import pandas as pd
import plotly.express as px


# IDENTIFICAR A AGREGAÇÃO
def suggest_aggregation(column_name):

    name = str(column_name).lower()

    average_terms = [
        "preco_unitario", "preço_unitário",
        "custo_unitario", "custo_unitário",
        "valor_unitario", "valor_unitário",
        "taxa", "percentual", "percent",
        "margem", "media", "média",
        "ticket_medio", "ticket_médio",
        "score", "nota"
    ]

    sum_terms = [
        "quantidade", "qtd", "volume",
        "total", "receita", "faturamento",
        "despesa", "custo", "venda",
        "investimento", "consumo"
    ]

    if any(term in name for term in average_terms):
        return "Média"

    if any(term in name for term in sum_terms):
        return "Soma"

    return "Média"


# IDENTIFICAR CANDIDATOS
def identify_chart_candidates(df):

    candidates = []

    date_columns = []
    numeric_columns = []
    categorical_columns = []

    for column in df.columns:

        series = df[column].dropna()

        if series.empty:
            continue

        name = str(column).lower()

        date_terms = [
            "data", "date", "timestamp",
            "periodo", "período"
        ]

        if (
            pd.api.types.is_datetime64_any_dtype(series)
            or any(term in name for term in date_terms)
        ):

            parsed = pd.to_datetime(
                series,
                errors="coerce",
                dayfirst=True
            )

            if parsed.notna().mean() >= 0.8:
                date_columns.append(column)
                continue

        if pd.api.types.is_numeric_dtype(series):

            numeric_columns.append(column)

        elif series.nunique() <= 30:

            categorical_columns.append(column)

    # GRÁFICOS TEMPORAIS
    for date_col in date_columns:

        for numeric_col in numeric_columns:

            candidates.append({
                "Tipo": "Linha",
                "Eixo X": date_col,
                "Eixo Y": numeric_col,
                "Agregação": suggest_aggregation(numeric_col),
                "Objetivo": "Analisar evolução temporal"
            })

    # GRÁFICOS COMPARATIVOS
    for category_col in categorical_columns:

        for numeric_col in numeric_columns:

            candidates.append({
                "Tipo": "Barras",
                "Eixo X": category_col,
                "Eixo Y": numeric_col,
                "Agregação": suggest_aggregation(numeric_col),
                "Objetivo": "Comparar valores por categoria"
            })

    # DISTRIBUIÇÃO NUMÉRICA
    for numeric_col in numeric_columns:

        candidates.append({
            "Tipo": "Histograma",
            "Eixo X": numeric_col,
            "Eixo Y": None,
            "Agregação": "Não aplicável",
            "Objetivo": "Analisar distribuição dos valores"
        })

    # FREQUÊNCIA CATEGÓRICA
    for category_col in categorical_columns:

        candidates.append({
            "Tipo": "Frequência",
            "Eixo X": category_col,
            "Eixo Y": None,
            "Agregação": "Contagem",
            "Objetivo": "Identificar categorias mais frequentes"
        })

    return pd.DataFrame(candidates)


# CONSTRUIR GRÁFICOS
def build_chart(df, candidate):

    chart_type = candidate["Tipo"]
    x_column = candidate["Eixo X"]
    y_column = candidate["Eixo Y"]

    if chart_type == "Linha":

        data = df[[x_column, y_column]].copy()

        data[x_column] = pd.to_datetime(
            data[x_column],
            errors="coerce",
            dayfirst=True
        )

        data = data.dropna()

        if data.empty:
            return None

        if candidate["Agregação"] == "Soma":
            grouped = data.groupby(x_column)[y_column].sum()
        else:
            grouped = data.groupby(x_column)[y_column].mean()

        grouped = grouped.reset_index().sort_values(x_column)

        fig = px.line(
            grouped,
            x=x_column,
            y=y_column,
            markers=True,
            title=f"Evolução de {y_column}"
        )

    elif chart_type == "Barras":

        data = df[[x_column, y_column]].dropna()

        if data.empty:
            return None

        if candidate["Agregação"] == "Soma":
            grouped = data.groupby(x_column)[y_column].sum()
        else:
            grouped = data.groupby(x_column)[y_column].mean()

        grouped = grouped.reset_index().sort_values(
            y_column,
            ascending=False
        )

        fig = px.bar(
            grouped,
            x=x_column,
            y=y_column,
            title=f"{y_column} por {x_column}"
        )

    elif chart_type == "Histograma":

        data = df[[x_column]].dropna()

        if data.empty:
            return None

        fig = px.histogram(
            data,
            x=x_column,
            title=f"Distribuição de {x_column}"
        )

    elif chart_type == "Frequência":

        grouped = (
            df[x_column]
            .value_counts()
            .reset_index()
        )

        grouped.columns = [x_column, "Frequência"]

        fig = px.bar(
            grouped,
            x=x_column,
            y="Frequência",
            title=f"Frequência de {x_column}"
        )

    else:
        return None

    fig.update_layout(
        template="plotly_white",
        xaxis_title=x_column,
        yaxis_title=y_column if y_column else "Frequência"
    )

    return fig


# PRIORIZAR INDICADORES
def score_candidate(candidate):

    score = 0

    chart_type = candidate["Tipo"]

    x_column = str(candidate["Eixo X"]).lower()

    y_column = str(candidate["Eixo Y"]).lower()

    important_terms = [
        "total", "receita", "faturamento",
        "investimento", "resultado"
    ]

    quantity_terms = [
        "quantidade", "volume", "qtd"
    ]

    if chart_type == "Linha":
        score += 100

    elif chart_type == "Barras":
        score += 80

    elif chart_type == "Histograma":
        score += 50

    elif chart_type == "Frequência":
        score += 40

    if any(term in y_column for term in important_terms):
        score += 30

    elif any(term in y_column for term in quantity_terms):
        score += 20

    if candidate["Agregação"] == "Soma":
        score += 10

    if "produto" in x_column or "regiao" in x_column:
        score += 5

    return score


# SELECIONAR OS GRÁFICOS MAIS RELEVANTES
def select_best_candidates(candidates, limit=5):

    if candidates.empty:
        return candidates

    candidates = candidates.copy()

    candidates["_Score"] = candidates.apply(
        lambda row: score_candidate(row),
        axis=1
    )

    selected = []

    # UM GRÁFICO TEMPORAL
    lines = candidates[
        candidates["Tipo"] == "Linha"
    ].sort_values("_Score", ascending=False)

    if not lines.empty:
        selected.append(lines.iloc[0])

    # DOIS GRÁFICOS COMPARATIVOS
    bars = candidates[
        candidates["Tipo"] == "Barras"
    ].sort_values("_Score", ascending=False)

    used_categories = set()

    for _, row in bars.iterrows():

        category = row["Eixo X"]

        if category not in used_categories:

            selected.append(row)
            used_categories.add(category)

        if len(used_categories) >= 2:
            break

    # UM HISTOGRAMA
    histograms = candidates[
        candidates["Tipo"] == "Histograma"
    ].sort_values("_Score", ascending=False)

    if not histograms.empty:
        selected.append(histograms.iloc[0])

    # UMA ANÁLISE DE FREQUÊNCIA
    frequencies = candidates[
        candidates["Tipo"] == "Frequência"
    ].sort_values("_Score", ascending=False)

    if not frequencies.empty:
        selected.append(frequencies.iloc[0])

    result = pd.DataFrame(selected)

    return result.head(limit)


# GERAR GRÁFICOS
def generate_charts(df, limit=5):

    candidates = identify_chart_candidates(df)

    selected = select_best_candidates(
        candidates,
        limit=limit
    )

    charts = []

    for _, candidate in selected.iterrows():

        fig = build_chart(df, candidate)

        if fig is not None:

            charts.append({
                "titulo": fig.layout.title.text,
                "tipo": candidate["Tipo"],
                "figura": fig
            })

    return charts