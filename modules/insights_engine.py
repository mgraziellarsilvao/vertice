import numpy as np
import pandas as pd

from modules.chart_engine import suggest_aggregation
from modules.column_rules import is_identifier_column


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
# 4. ANÁLISE DE ANOMALIAS (IQR)
# =========================================================

# Tamanho mínimo de um grupo para calcular o IQR dentro dele.
# Com poucos registros os quartis ficam instáveis.
MIN_GROUP_SIZE = 8


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


def list_group_columns(df, min_group=MIN_GROUP_SIZE):

    """
    Lista as colunas de categoria que servem para agrupar
    o cálculo do IQR: precisam ter pelo menos dois grupos
    com o tamanho mínimo e não podem ser identificadores.
    """

    options = []

    for column in identify_columns(df)["categoricas"]:

        if is_identifier_column(column):
            continue

        sizes = df[column].value_counts()

        if len(sizes) >= 2 and (sizes >= min_group).sum() >= 2:
            options.append(column)

    return options


def find_anomalies(
    df,
    numeric_columns,
    group_col=None,
    min_group=MIN_GROUP_SIZE
):

    """
    Aplica o IQR a cada coluna numérica.

    - group_col=None: os limites são calculados sobre a coluna inteira.
    - group_col informado: os limites são calculados dentro de cada
      grupo da categoria. Grupos menores que min_group não são avaliados.

    Retorna os registros sinalizados e, para cada indicador,
    quantos grupos foram avaliados em relação ao total.
    """

    columns_out = [
        "posicao", "Indicador", "Valor",
        "Limite inferior", "Limite superior", "Grupo"
    ]

    use_groups = group_col is not None and group_col in df.columns

    rows = []
    coverage = {}

    for order, column in enumerate(numeric_columns):

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        ).astype("float64")

        if use_groups and group_col != column:
            groups = df.groupby(group_col, dropna=True).indices
        else:
            groups = {None: np.arange(len(df))}

        evaluated = 0

        for group, positions in groups.items():

            group_values = values.iloc[positions]
            valid = group_values.dropna()

            if use_groups and len(valid) < min_group:
                continue

            limits = calculate_anomaly_limits(valid)

            if limits is None:
                continue

            evaluated += 1

            lower_limit, upper_limit = limits

            mask = (
                (group_values < lower_limit)
                | (group_values > upper_limit)
            ).to_numpy()

            for local in np.flatnonzero(mask):

                rows.append({
                    "_coluna": order,
                    "posicao": int(positions[local]),
                    "Indicador": column,
                    "Valor": float(group_values.iloc[local]),
                    "Limite inferior": lower_limit,
                    "Limite superior": upper_limit,
                    "Grupo": group
                })

        coverage[column] = (evaluated, len(groups))

    if not rows:
        return pd.DataFrame(columns=columns_out), coverage

    flagged = (
        pd.DataFrame(rows)
        .sort_values(["_coluna", "posicao"])
        .drop(columns="_coluna")
        .reset_index(drop=True)
    )

    return flagged[columns_out], coverage


def analyze_anomalies(
    df,
    columns,
    group_col=None,
    min_group=MIN_GROUP_SIZE
):

    insights = []

    flagged, coverage = find_anomalies(
        df,
        columns["numericas"],
        group_col,
        min_group
    )

    if flagged.empty:
        return insights

    for column, subset in flagged.groupby("Indicador", sort=False):

        count = len(subset)

        if group_col is None:

            lower_limit = subset["Limite inferior"].iloc[0]
            upper_limit = subset["Limite superior"].iloc[0]

            insight = (
                f"Foram identificados {count} "
                f"valores atípicos em {column}."
            )

            evidence = (
                f"Limite inferior: {lower_limit:.2f} | "
                f"Limite superior: {upper_limit:.2f} | "
                f"Valores atípicos: {count}"
            )

        else:

            evaluated, total = coverage[column]

            insight = (
                f"Foram identificados {count} valores atípicos "
                f"em {column}, comparando cada registro com os "
                f"demais do mesmo grupo de {group_col}."
            )

            evidence = (
                f"Método: IQR por {group_col} | "
                f"Grupos avaliados: {evaluated} de {total} | "
                f"Valores atípicos: {count}"
            )

        insights.append({
            "Tipo": "Anomalia",
            "Indicador": column,
            "Agregação": "Não aplicável",
            "Insight": insight,
            "Evidência": evidence,
            "Atenção": (
                "Investigar os registros identificados. "
                "Valores atípicos não significam necessariamente erros."
            )
        })

    return insights


# =========================================================
# 5. DETALHAMENTO DOS REGISTROS ATÍPICOS
# =========================================================

def generate_anomaly_details(
    df,
    group_col=None,
    min_group=MIN_GROUP_SIZE
):

    use_groups = group_col is not None and group_col in df.columns

    detail_columns = ["Linha na base", "Indicador"]

    if use_groups:
        detail_columns.append("Grupo")

    detail_columns += [
        "Valor atípico",
        "Classificação",
        "Limite inferior",
        "Limite superior"
    ]

    if df.empty:
        return pd.DataFrame(columns=detail_columns)

    columns = identify_columns(df)

    flagged, _ = find_anomalies(
        df,
        columns["numericas"],
        group_col,
        min_group
    )

    if flagged.empty:
        return pd.DataFrame(columns=detail_columns)

    details = []

    for _, item in flagged.iterrows():

        position = int(item["posicao"])
        value = item["Valor"]

        classification = (
            "Abaixo do limite inferior"
            if value < item["Limite inferior"]
            else "Acima do limite superior"
        )

        record = df.iloc[position].to_dict()

        record.update({
            "Linha na base": position + 1,
            "Indicador": item["Indicador"],
            "Valor atípico": value,
            "Classificação": classification,
            "Limite inferior": item["Limite inferior"],
            "Limite superior": item["Limite superior"]
        })

        if use_groups:
            record["Grupo"] = item["Grupo"]

        details.append(record)

    result = pd.DataFrame(details)

    original_columns = [
        column
        for column in result.columns
        if column not in detail_columns
    ]

    return result[detail_columns + original_columns]


# =========================================================
# 6. GERAÇÃO CONSOLIDADA DOS INSIGHTS
# =========================================================

def generate_insights(
    df,
    group_col=None,
    min_group=MIN_GROUP_SIZE
):

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
        analyze_anomalies(df, columns, group_col, min_group)
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
