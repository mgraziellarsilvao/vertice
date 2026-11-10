import pandas as pd

def _date_ratio(series):
    sample = series.dropna().astype(str).head(200)
    if sample.empty:
        return 0.0
    return float(pd.to_datetime(sample, errors="coerce", dayfirst=True).notna().mean())

def identify_column_type(series, column_name=""):
    if pd.api.types.is_bool_dtype(series):
        return "Booleano"
    if pd.api.types.is_numeric_dtype(series):
        return "Numérico"
    vals = set(series.dropna().astype(str).str.strip().str.lower().unique())
    if vals and vals.issubset({"true", "false", "0", "1", "sim", "não", "nao", "yes", "no"}):
        return "Booleano"
    name = str(column_name).lower()
    hints = ("data", "date", "dia", "mês", "mes", "ano", "timestamp")
    ratio = _date_ratio(series)
    if (any(h in name for h in hints) and ratio >= 0.5) or ratio >= 0.85:
        return "Data"
    non_null = series.dropna()
    if non_null.empty:
        return "Sem dados"
    unique = non_null.nunique()
    if unique <= 30 or unique / len(non_null) <= 0.05:
        return "Categoria"
    return "Texto"

def profile_dataframe(df):
    rows = []
    for col in df.columns:
        s = df[col]
        examples = " | ".join(s.dropna().astype(str).drop_duplicates().head(3).tolist())
        rows.append({
            "Coluna": str(col), "Tipo original": str(s.dtype),
            "Tipo identificado": identify_column_type(s, col),
            "Valores preenchidos": int(s.notna().sum()),
            "Valores vazios": int(s.isna().sum()),
            "Valores distintos": int(s.nunique(dropna=True)),
            "Exemplos": examples[:160]
        })
    return pd.DataFrame(rows)
