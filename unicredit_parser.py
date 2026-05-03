# unicredit_parser.py

import re
from pdfminer.high_level import extract_text


# ---------------------------------------------------------
# 1) Extract text from PDF
# ---------------------------------------------------------
def extract_unicredit_text(pdf_bytes: bytes) -> str:
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)

    try:
        text = extract_text(temp_path)
    except Exception as e:
        return f"[Грешка при извличане]: {e}"

    return text


# ---------------------------------------------------------
# 2) Parse UniCredit transactions
# ---------------------------------------------------------
def parse_unicredit_transactions(text: str):
    """
    Parse the UniCredit 'Платежни операции' table from extracted text.
    Returns a list of dicts with structured transaction data.
    """

    # Normalize whitespace
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Find start of the table
    start_idx = None
    for i, line in enumerate(lines):
        if "Платежни операции" in line or "Payment transactions" in line:
            start_idx = i
            break

    if start_idx is None:
        return []

    # Extract only the table part
    table_lines = lines[start_idx + 1 :]

    # Stop when next section begins
    stop_keywords = [
        "Извлечението е автоматично генерирано",
        "Важно за Вашето обслужване",
        "Your deposits in UniCredit",
    ]

    cleaned = []
    for line in table_lines:
        if any(k in line for k in stop_keywords):
            break
        cleaned.append(line)

    # Remove header rows
    cleaned = [
        l for l in cleaned
        if not ("Дата" in l or "Description" in l or "Type" in l or "EUR" in l)
    ]

    # ---------------------------------------------------------
    # 3) Parse rows
    # ---------------------------------------------------------
    transactions = []
    buffer = None  # holds first row of 2-row transaction

    date_regex = r"^\d{2}\.\d{2}\.\d{4}"
    eur_regex = r"(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})$"

    for line in cleaned:
        # Detect start of a new transaction row
        if re.match(date_regex, line):
            # If previous buffer exists → save it
            if buffer:
                transactions.append(buffer)
                buffer = None

            parts = line.split()
            date = parts[0]
            # Remove date and value date
            rest = " ".join(parts[2:])

            # Extract EUR amount
            eur_match = re.search(eur_regex, rest)
            eur = eur_match.group(1).replace(",", "") if eur_match else ""

            # Remove EUR from description
            if eur:
                rest = rest[: rest.rfind(eur)].strip()

            # Extract transaction number (last token if alphanumeric)
            tokens = rest.split()
            trx = tokens[-1] if re.match(r"[A-Za-z0-9]+", tokens[-1]) else ""
            if trx:
                rest = " ".join(tokens[:-1])

            # Extract type (DT/CT)
            type_match = re.search(r"\b(ДТ|КТ|DT|CT)\b", rest)
            op_type = type_match.group(1) if type_match else ""

            # Remove type from description
            if op_type:
                rest = rest.replace(op_type, "").strip()

            buffer = {
                "date": date,
                "description": rest,
                "type": op_type,
                "eur": eur,
                "transaction_id": trx,
            }

        else:
            # This is second row of a 2-row transaction → append to description
            if buffer:
                buffer["description"] += " " + line.strip()

    # Add last buffered transaction
    if buffer:
        transactions.append(buffer)

    return transactions
