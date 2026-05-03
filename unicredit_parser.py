import re
import pandas as pd
from pdfminer.high_level import extract_text


def extract_unicredit_text(pdf_bytes: bytes) -> str:
    """Extract text from UniCredit PDF using pdfminer."""
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)
    return extract_text(temp_path)


def parse_unicredit_transactions(text: str):
    """
    Parse UniCredit PDF text extracted by pdfminer.
    Works with the block-structured format (dates block, descriptions block, types block, EUR block, trx block).
    Returns list of dicts with: date, description, type, eur, transaction_id.
    """

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # -----------------------------
    # 1) Extract dates (always pairs)
    # -----------------------------
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    dates = [l for l in lines if re.match(date_pattern, l)]

    # Keep only the first date of each pair (date / value date)
    dates = dates[::2]

    # -----------------------------
    # 2) Extract types (ДТ/КТ)
    # -----------------------------
    types = []
    for l in lines:
        if l in ("ДТ", "DT", "КТ", "CT"):
            types.append(l)

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
    # Descriptions are between date blocks and type blocks.
    # -----------------------------
    descriptions = []
    current_desc = []

    for l in lines:
        if re.match(date_pattern, l):
            if current_desc:
                descriptions.append(" ".join(current_desc))
                current_desc = []
            continue

        if l in ("ДТ", "DT", "КТ", "CT"):
            if current_desc:
                descriptions.append(" ".join(current_desc))
                current_desc = []
            continue

        # Description lines start with "-"
        if l.startswith("-"):
            current_desc.append(l)

    if current_desc:
        descriptions.append(" ".join(current_desc))

    # -----------------------------
    # Align all lists by index
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
