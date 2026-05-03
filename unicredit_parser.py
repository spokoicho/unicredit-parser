import re
import pandas as pd
from pdfminer.high_level import extract_text


def extract_unicredit_text(pdf_bytes: bytes) -> str:
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)
    return extract_text(temp_path)


def parse_unicredit_transactions(text: str):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # -----------------------------
    # 1) Extract dates (first of each pair)
    # -----------------------------
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    all_dates = [l for l in lines if re.match(date_pattern, l)]
    dates = all_dates[::2]  # keep only the first of each pair

    # -----------------------------
    # 2) Extract types (ДТ/КТ)
    # -----------------------------
    types = [l for l in lines if l in ("ДТ", "DT", "КТ", "CT")]

    # -----------------------------
    # 3) Extract EUR amounts
    # -----------------------------
    eur_pattern = r"^\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2}$"
    eur_values = [l.replace(",", "") for l in lines if re.match(eur_pattern, l)]

    # -----------------------------
    # 4) Extract transaction IDs
    # -----------------------------
    trx_pattern = r"^[A-Za-z0-9]{10,}$"
    trx_ids = [l for l in lines if re.match(trx_pattern, l)]

    # -----------------------------
    # 5) Extract descriptions
    # -----------------------------
    descriptions = []
    current = []

    for l in lines:
        if re.match(date_pattern, l) or l in ("ДТ", "DT", "КТ", "CT"):
            if current:
                descriptions.append(" ".join(current))
                current = []
            continue

        if l.startswith("-"):
            current.append(l)

    if current:
        descriptions.append(" ".join(current))

    # -----------------------------
    # 6) Align by index
    # -----------------------------
    n = min(len(dates), len(descriptions), len(types), len(eur_values), len(trx_ids))

    result = []
    for i in range(n):
        result.append({
            "date": dates[i],
            "description": descriptions[i],
            "type": types[i],
            "eur": eur_values[i],
            "transaction_id": trx_ids[i]
        })

    return result
