import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal


# ================================
# 1) Layout extraction (табличен модел)
# ================================
def extract_layout_rows(pdf_bytes):
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)

    elements = []

    # Извличаме всички текстови елементи с координати
    for page_layout in extract_pages(temp_path):
        for element in page_layout:
            if isinstance(element, (LTTextBoxHorizontal, LTTextLineHorizontal)):
                text = element.get_text().strip()
                if text:
                    elements.append({
                        "text": text,
                        "x0": element.x0,
                        "y0": element.y0,
                        "x1": element.x1,
                        "y1": element.y1
                    })

    # Групиране по редове чрез Y-координата
    rows = []
    current_row = []
    last_y = None
    tolerance = 3

    for el in sorted(elements, key=lambda e: -e["y0"]):
        if last_y is None:
            current_row = [el]
            last_y = el["y0"]
            continue

        if abs(el["y0"] - last_y) <= tolerance:
            current_row.append(el)
        else:
            rows.append(current_row)
            current_row = [el]
            last_y = el["y0"]

    if current_row:
        rows.append(current_row)

    # Сортиране по X вътре в реда
    sorted_rows = []
    for row in rows:
        sorted_rows.append(sorted(row, key=lambda e: e["x0"]))

    return sorted_rows


# ================================
# 2) Помощни функции
# ================================
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


# ================================
# 3) Главен UniCredit парсер
# ================================
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

    # 6) Контрагент + основание
    for op in operations:
        op["description"] = op["description"].strip()
        op["counterparty"] = extract_counterparty(op["description"])
        op["basis"] = extract_basis(op["description"])

    return operations
