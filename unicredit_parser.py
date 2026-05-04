import re
from unicredit_layout import extract_layout_rows


DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}")
EUR_RE = re.compile(r"^\d{1,3}(?:[.,]\d{3})*[.,]\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9]{10,}$")
TYPE_RE = re.compile(r"^(ДТ|КТ|DT|CT)$")


def clean_date(cell):
    if "/" in cell:
        return cell.split("/")[0].strip()
    return cell.strip()


def extract_counterparty(description):
    # ATM → контрагент = UniCredit Bulbank
    if "АТМ" in description or "ATM" in description:
        return "UniCredit Bulbank"

    # Контрагент : ИМЕ
    m = re.search(r"Контрагент\s*:\s*([A-Za-zА-Яа-я0-9\s\.\-]+)", description)
    if m:
        return m.group(1).strip()

    # IBAN / ИМЕ / ф-ра
    m = re.search(r"/\s*([^/]+?)\s*(ф-ра|$)", description)
    if m:
        return m.group(1).strip()

    return ""


def extract_basis(description):
    # ATM
    if "АТМ" in description or "ATM" in description:
        return "Теглене АТМ"

    # ф-ра <номер>
    m = re.search(r"ф-ра\s*([A-Za-z0-9]+)", description)
    if m:
        return f"ф-ра {m.group(1)}"

    return ""


def parse_unicredit(pdf_bytes):
    rows = extract_layout_rows(pdf_bytes)

    operations = []
    current = {
        "date": "",
        "description": "",
        "type": "",
        "eur": "",
        "transaction_id": ""
    }

    for row in rows:
        texts = [c["text"] for c in row]

        # 1) Дата → начало на нова операция
        if DATE_RE.match(texts[0]):
            # ако има текуща операция → записваме я
            if current["date"]:
                operations.append(current)

            current = {
                "date": clean_date(texts[0]),
                "description": "",
                "type": "",
                "eur": "",
                "transaction_id": ""
            }
            continue

        # 2) Описание (винаги започва с "-")
        if texts[0].startswith("-"):
            current["description"] += " " + " ".join(texts)
            continue

        # 3) Тип
        for t in texts:
            if TYPE_RE.match(t):
                current["type"] = t

        # 4) EUR
        for t in texts:
            if EUR_RE.match(t.replace(",", "")):
                current["eur"] = t.replace(",", "")

        # 5) Transaction ID
        for t in texts:
            if ID_RE.match(t):
                current["transaction_id"] = t

    # последната операция
    if current["date"]:
        operations.append(current)

    # извличане на контрагент и основание
    for op in operations:
        op["description"] = op["description"].strip()
        op["counterparty"] = extract_counterparty(op["description"])
        op["basis"] = extract_basis(op["description"])

    return operations
