import numpy as np
import pandas as pd

from modules.chart_engine import suggest_aggregation


OUTPUT_COLUMNS = [
    "Tipo",
    "Indicador",
    "Agregação",
    "Insight",
    "Evidência",
    "Atenção"
]


# =========================================================
# 1. IDENTIFICAÇÃO DAS COLUNAS
# =========================================================

def is_identifier_column(column_name):

    name = str(column_name).lower().strip()

    identifiers = [
        "id",
        "codigo",
        "código",
        "cod_",
        "cpf",
        "cnpj",
        "cep",
        "telefone",
        "numero_pedido",
        "numero_ordem"
    ]

    return any(term in name for term in identifiers)


def is_boolean_series(series):

    """
    Identifica colunas booleanas pelo dtype ou pelo conteúdo.
    Também reconhece booleanos armazenados como object.
    """

    if pd.api.types.is_bool_dtype(series.dtype):
        return True

    values = series.dropna()

    if values.empty:
        return False

    return values.map(
        lambda value: isinstance(value, (bool, np.bool_))
    ).all()


def identify_columns(df):

    date_columns = []
    numeric_columns = []
    category_columns = []

    for column in df.columns:

        series = df[column].dropna()

        if series.empty:
            continue

        name = str(column).lower()

        # BOOLEANOS: identificar antes dos demais tipos

        if is_boolean_series(series):

            category_columns.append(column)
            continue

        # DATAS

        date_terms = [
            "data",
            "date",
            "timestamp",
            "periodo",
            "período"
        ]

        if (
            pd.api.types.is_datetime64_any_dtype(series)
            or any(term in name for term in date_terms)
        ):

            dates = pd.to_datetime(
                series,
                errors="coerce",
                dayfirst=True
            )

            if dates.notna().mean() >= 0.8:
                date_columns.append(column)
                continue

        # NUMÉRICOS

        if pd.api.types.is_numeric_dtype(series):

            if not is_identifier_column(column):
                numeric_columns.append(column)

        # CATEGÓRICOS

        elif (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
            or isinstance(series.dtype, pd.CategoricalDtype)
        ):

            if series.nunique() <= 30:
                category_columns.append(column)

    return {
        "datas": date_columns,
        "numericas": numeric_columns,
        "categoricas": category_columns
    }


# =========================================================
# 2. ANÁLISE DE TENDÊNCIAS
# =========================================================

def analyze_trends(df, columns):

    insights = []

    date_columns = columns["datas"]
    numeric_columns = columns["numericas"]

    if not date_columns or not numeric_columns:
        return insights

    date_col = date_columns[0]

    for numeric_col in numeric_columns:

        aggregation = suggest_aggregation(numeric_col)

        temp = df[[date_col, numeric_col]].copy()

        temp[date_col] = pd.to_datetime(
            temp[date_col],
            errors="coerce",
            dayfirst=True
        )

        temp[numeric_col] = pd.to_numeric(
            temp[numeric_col],
            errors="coerce"
        )

        temp = temp.dropna()

        if temp.empty:
            continue

        if aggregation == "Soma":

            grouped = (
                temp.groupby(temp[date_col].dt.date)[numeric_col]
                .sum()
                .sort_index()
            )

        else:

            grouped = (
                temp.groupby(temp[date_col].dt.date)[numeric_col]
                .mean()
                .sort_index()
            )

        if len(grouped) < 4:
            continue

        midpoint = len(grouped) // 2

        previous_values = grouped.iloc[:midpoint]
        current_values = grouped.iloc[midpoint:]

        previous = previous_values.mean()
        current = current_values.mean()

        if previous == 0:
            continue

        variation = (
            (current - previous) / abs(previous)
        ) * 100

        if abs(variation) < 5:
            continue

        direction = (
            "aumentou"
            if variation > 0
            else "diminuiu"
        )

        if aggregation == "Soma":

            insight = (
                f"A média diária dos valores de {numeric_col} "
                f"{direction} {abs(variation):.1f}% "
                "na comparação entre as duas metades "
                "do período analisado."
            )

            evidence = (
                f"Média diária anterior: {previous:.2f} | "
                f"Média diária recente: {current:.2f}"
            )

        else:

            insight = (
                f"A média de {numeric_col} "
                f"{direction} {abs(variation):.1f}% "
                "na comparação entre as duas metades "
                "do período analisado."
            )

            evidence = (
                f"Média anterior: {previous:.2f} | "
                f"Média recente: {current:.2f}"
            )

        insights.append({
            "Tipo": "Tendência",
            "Indicador": numeric_col,
            "Agregação": aggregation,
            "Insight": insight,
            "Evidência": evidence,
            "Atenção": "Verificar possíveis causas da variação."
        })

    return insights


# =========================================================
# 3. ANÁLISE DE CONCENTRAÇÃO
# =========================================================

def analyze_concentration(df, columns):

    insights = []

    numeric_columns = columns["numericas"]
    category_columns = columns["categoricas"]

    for numeric_col in numeric_columns:

        aggregation = suggest_aggregation(numeric_col)

        if aggregation != "Soma":
            continue

        for category_col in category_columns:

            temp = df[[category_col, numeric_col]].copy()

            temp[numeric_col] = pd.to_numeric(
                temp[numeric_col],
                errors="coerce"
            )

            temp = temp.dropna()

            if temp.empty:
                continue

            grouped = (
                temp.groupby(category_col)[numeric_col]
                .sum()
                .sort_values(ascending=False)
            )

            total = grouped.sum()

            if total <= 0:
                continue

            top_category = grouped.index[0]
            top_value = grouped.iloc[0]

            participation = (top_value / total) * 100

            if participation >= 40:

                insights.append({
                    "Tipo": "Concentração",
                    "Indicador": numeric_col,
                    "Agregação": aggregation,
                    "Insight": (
                        f"A categoria '{top_category}' representa "
                        f"{participation:.1f}% do total de "
                        f"{numeric_col}."
                    ),
                    "Evidência": (
                        f"Categoria principal: {top_category} | "
                        f"Valor: {top_value:.2f} | "
                        f"Total: {total:.2f}"
                    ),
                    "Atenção": (
                        "Avaliar a concentração e sua relevância "
                        "para o negócio."
                    )
                })

    return insights


# =========================================================
# 4. ANÁLISE DE ANOMALIAS
# =========================================================

def calculate_anomaly_limits(series):

    """
    Calcula os limites IQR somente para séries quantitativas.
    Protege contra booleanos e valores não numéricos.
    """

    # Impedir que booleanos participem dos quartis

    if is_boolean_series(series):
        return None

    # Converter explicitamente para valores numéricos

    numeric_series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(numeric_series) < 5:
        return None

    # Garantir que o NumPy receba valores float64

    numeric_series = pd.Series(
        numeric_series.astype("float64").to_numpy()
    )

    q1 = numeric_series.quantile(0.25)
    q3 = numeric_series.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        return None

    lower_limit = q1 - (1.5 * iqr)
    upper_limit = q3 + (1.5 * iqr)

    return lower_limit, upper_limit


def analyze_anomalies(df, columns):

    insights = []

    for numeric_col in columns["numericas"]:

        series = pd.to_numeric(
            df[numeric_col],
            errors="coerce"
        ).dropna()

        if len(series) < 5:
            continue

        # Garantir tipo numérico convencional

        series = series.astype("float64")

        limits = calculate_anomaly_limits(series)

        if limits is None:
            continue

        lower_limit, upper_limit = limits

        anomalies = series[
            (series < lower_limit)
            | (series > upper_limit)
        ]

        if anomalies.empty:
            continue

        insights.append({
            "Tipo": "Anomalia",
            "Indicador": numeric_col,
            "Agregação": "Não aplicável",
            "Insight": (
                f"Foram identificados {len(anomalies)} "
                f"valores atípicos em {numeric_col}."
            ),
            "Evidência": (
                f"Limite inferior: {lower_limit:.2f} | "
                f"Limite superior: {upper_limit:.2f} | "
                f"Valores atípicos: {len(anomalies)}"
            ),
            "Atenção": (
                "Investigar os registros identificados. "
                "Valores atípicos não significam necessariamente erros."
            )
        })

    return insights


# =========================================================
# 5. DETALHAMENTO DOS REGISTROS ATÍPICOS
# =========================================================

def generate_anomaly_details(df):

    detail_columns = [
        "Linha na base",
        "Indicador",
        "Valor atípico",
        "Classificação",
        "Limite inferior",
        "Limite superior"
    ]

    if df.empty:
        return pd.DataFrame(columns=detail_columns)

    columns = identify_columns(df)

    details = []

    for numeric_col in columns["numericas"]:

        series = pd.to_numeric(
            df[numeric_col],
            errors="coerce"
        )

        series = series.astype("float64")

        valid_series = series.dropna()

        if len(valid_series) < 5:
            continue

        limits = calculate_anomaly_limits(valid_series)

        if limits is None:
            continue

        lower_limit, upper_limit = limits

        anomaly_mask = (
            (series < lower_limit)
            | (series > upper_limit)
        )

        positions = [
            position
            for position, is_anomaly in enumerate(
                anomaly_mask.fillna(False).tolist()
            )
            if is_anomaly
        ]

        for position in positions:

            value = series.iloc[position]

            classification = (
                "Abaixo do limite inferior"
                if value < lower_limit
                else "Acima do limite superior"
            )

            record = df.iloc[position].to_dict()

            record.update({
                "Linha na base": position + 1,
                "Indicador": numeric_col,
                "Valor atípico": value,
                "Classificação": classification,
                "Limite inferior": lower_limit,
                "Limite superior": upper_limit
            })

            details.append(record)

    if not details:
        return pd.DataFrame(columns=detail_columns)

    result = pd.DataFrame(details)

    metadata_columns = detail_columns

    original_columns = [
        column
        for column in result.columns
        if column not in metadata_columns
    ]

    return result[
        metadata_columns + original_columns
    ]


# =========================================================
# 6. GERAÇÃO CONSOLIDADA DOS INSIGHTS
# =========================================================

def generate_insights(df):

    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    columns = identify_columns(df)

    insights = []

    insights.extend(
        analyze_trends(df, columns)
    )

    insights.extend(
        analyze_concentration(df, columns)
    )

    insights.extend(
        analyze_anomalies(df, columns)
    )

    if not insights:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    result = pd.DataFrame(insights)

    priority = {
        "Tendência": 1,
        "Concentração": 2,
        "Anomalia": 3
    }

    result["_ordem"] = result["Tipo"].map(priority)

    result = (
        result.sort_values("_ordem")
        .drop(columns="_ordem")
        .reset_index(drop=True)
    )

    return result