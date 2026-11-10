import pandas as pd


def is_identifier_column(column_name):
    name = str(column_name).lower()

    identifiers = [
        "id", "codigo", "código", "cod_",
        "cpf", "cnpj", "cep", "telefone",
        "numero_pedido", "numero_ordem"
    ]

    return any(term in name for term in identifiers)


def detect_date_column(column_name, series):
    name = str(column_name).lower()

    date_terms = [
        "data", "date", "timestamp",
        "periodo", "período"
    ]

    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    if any(term in name for term in date_terms):
        dates = pd.to_datetime(
            series,
            errors="coerce",
            dayfirst=True
        )

        valid_ratio = dates.notna().mean()

        if valid_ratio >= 0.8:
            return dates

    return None


def generate_metrics(df):

    metrics = []

    for column in df.columns:

        series = df[column].dropna()

        if series.empty:
            continue

        # IDENTIFICAR DATAS

        dates = detect_date_column(column, series)

        if dates is not None:

            valid_dates = dates.dropna()

            if not valid_dates.empty:

                metrics.extend([
                    {
                        "Coluna": column,
                        "Métrica": "Data inicial",
                        "Valor": str(valid_dates.min().date())
                    },
                    {
                        "Coluna": column,
                        "Métrica": "Data final",
                        "Valor": str(valid_dates.max().date())
                    },
                    {
                        "Coluna": column,
                        "Métrica": "Dias distintos",
                        "Valor": int(valid_dates.nunique())
                    }
                ])

            continue

        # IDENTIFICAR COLUNAS BOOLEANAS

        is_boolean = pd.api.types.is_bool_dtype(series)

        # MÉTRICAS NUMÉRICAS

        if (
            pd.api.types.is_numeric_dtype(series)
            and not is_boolean
        ):

            if is_identifier_column(column):
                continue

            metrics.extend([
                {
                    "Coluna": column,
                    "Métrica": "Soma",
                    "Valor": round(float(series.sum()), 2)
                },
                {
                    "Coluna": column,
                    "Métrica": "Média",
                    "Valor": round(float(series.mean()), 2)
                },
                {
                    "Coluna": column,
                    "Métrica": "Mediana",
                    "Valor": round(float(series.median()), 2)
                },
                {
                    "Coluna": column,
                    "Métrica": "Mínimo",
                    "Valor": round(float(series.min()), 2)
                },
                {
                    "Coluna": column,
                    "Métrica": "Máximo",
                    "Valor": round(float(series.max()), 2)
                },
                {
                    "Coluna": column,
                    "Métrica": "Desvio-padrão",
                    "Valor": round(float(series.std()), 2)
                }
            ])

        # MÉTRICAS CATEGÓRICAS E BOOLEANAS

        elif (
            is_boolean
            or pd.api.types.is_object_dtype(series)
            or isinstance(series.dtype, pd.CategoricalDtype)
            or pd.api.types.is_string_dtype(series)
        ):

            frequencies = series.astype(str).value_counts()

            metrics.extend([
                {
                    "Coluna": column,
                    "Métrica": "Categorias distintas",
                    "Valor": int(series.nunique())
                },
                {
                    "Coluna": column,
                    "Métrica": "Categoria mais frequente",
                    "Valor": str(frequencies.index[0])
                },
                {
                    "Coluna": column,
                    "Métrica": "Frequência da categoria principal",
                    "Valor": int(frequencies.iloc[0])
                }
            ])

    return pd.DataFrame(metrics)