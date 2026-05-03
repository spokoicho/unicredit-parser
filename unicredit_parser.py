import re
import pandas as pd
from pdfminer.high_level import extract_text


# ---------------------------------------------------------
# Extract text from PDF
# ---------------------------------------------------------
def extract_unicredit_text(pdf_bytes: bytes) -> str:
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)
    return extract_text(temp_path)


# ---------------------------------------------------------
# Main UniCredit parser
# ---------------------------------------------------------
def parse_unicredit_transactions(text: str):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # -----------------------------
    # 1) Extract all dates
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
    # 5) Extract descriptions (split by "-")
    # -----------------------------
    descriptions = []
    current = []

    for l in lines:
        if l.startswith("-"):
            if current:
                descriptions.append(" ".join(current))
                current = []
            current.append(l)
        else:
            if current:
                current.append(l)

    if current:
        descriptions.append(" ".join(current))

    # -----------------------------
    # 6) Extract counterparty
    # Two formats:
    #   A) IBAN / Контрагент / ф-ра
    #   B) "Контрагент :" + next lines
    # -----------------------------
    counterparties = []

    for desc in descriptions:
        # Format B: "Контрагент :"
        m = re.search(r"Контрагент\s*:\s*([A-Za-zА-Яа-я0-9\s]+)", desc)
        if m:
            name = m.group(1).strip()
            name = re.sub(r"\s+\d{6,}$", "", name)  # remove trailing IDs
            counterparties.append(name)
            continue

        # Format A: IBAN / NAME / ф-ра
        m = re.search(r"/\s*([^/]+?)\s*(ф-ра|$)", desc)
        if m:
            name = m.group(1).strip()
            counterparties.append(name)
            continue

        counterparties.append("")

    # -----------------------------
    # 7) Extract basis (ф-ра <номер>)
    # -----------------------------
    basis_list = []
    for desc in descriptions:
        m = re.search(r"ф-ра\s*([A-Za-z0-9]+)", desc)
        if m:
            basis_list.append(f"ф-ра {m.group(1)}")
        else:
            basis_list.append("")

    # -----------------------------
    # 8) Align all lists by index
    # -----------------------------
    n = min(len(dates), len(descriptions), len(types), len(eur_values), len(trx_ids))

    result = []
    for i in range(n):
        result.append({
            "date": dates[i],
            "counterparty": counterparties[i],
            "basis": basis_list[i],
            "description": descriptions[i],
            "type": types[i],
            "eur": eur_values[i],
            "transaction_id": trx_ids[i]
        })

    return result
