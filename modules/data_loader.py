from pathlib import Path
import pandas as pd

def load_uploaded_file(uploaded_file, sheet_name=None):
    suffix = Path(getattr(uploaded_file, "name", str(uploaded_file))).suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(uploaded_file, sheet_name=sheet_name)
    if suffix == ".csv":
        error = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, sep=None, engine="python", encoding=encoding)
            except Exception as exc:
                error = exc
        raise ValueError(f"Falha ao ler o CSV. Último erro: {error}")
    raise ValueError("Formato não suportado. Use CSV, XLSX ou XLS.")
