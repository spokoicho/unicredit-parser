import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal


# ============================================================
# 1) Layout extraction – филтриране само на таблицата
# ============================================================

def extract_table_rows(pdf_bytes):
    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)

    elements = []

    # Извличаме всички текстови елементи
    for page_layout in extract_pages(temp_path):
        for el in page_layout:
            if isinstance(el, (LTTextBoxHorizontal, LTTextLineHorizontal)):
                text = el.get_text().strip()
                if not text:
                    continue

                # Филтър: таблицата винаги е в лявата част (x0 < 500)
                if el.x0 > 500:
                    continue

                # Филтър: игнорирай header-и и footer-и
                if "Извлечение" in text or "Statement" in text:
                    continue
                if "Дата/Вальор" in text:
                    continue
                if "Тип" in text and "EUR" in text:
                    continue
                if "Уважаеми" in text:
                    continue
                if "Влоговете Ви" in text:
                    continue

                elements.append({
                    "text": text,
                    "x0": el.x0,
                    "y0": el.y0,
                    "x1": el.x1,
                    "y1": el.y1
                })

    # Групиране по редове чрез Y-координата
    rows = []
    current = []
    last_y = None
    tolerance = 3

    for el in sorted(elements, key=lambda e: -e["y0"]):
        if last_y is None:
            current = [el]
            last_y = el["y0"]
            continue

        if abs(el["y0"] - last_y) <= tolerance:
            current.append(el)
        else:
            rows.append(current)
            current = [el]
            last_y = el["y0"]

    if current:
        rows.append(current)

    # Сортиране по X вътре в реда
    clean_rows = []
    for row in rows:
        clean_rows.append(sorted(row, key=lambda e: e["x0"]))

    return clean_rows


# ============================================================
# 2) Помощни функции
# ============================================================

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}")
EUR_RE = re.compile(r"^\d{1,3}(?:[.,]\d{3})*[.,]\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9]{10,}$")
TYPE_RE = re.compile(r"^(ДТ|КТ|DT|CT)$")


def merge_date_cells(texts):
    """Обединява двуредовите клетки 'Дата/Вальор'."""
    dates = [t for t in texts if DATE_RE.match(t)]
    if not dates:
        return None
    return dates[0]  # взимаме само първата дата


def extract_counterparty(desc):
    if "АТМ" in desc or "ATM" in desc:
        return "UniCredit Bulbank"

    m = re.search(r"Контрагент\s*:\s*([A-Za-zА-Яа-я0-9\s\.\-]+)", desc)
    if m:
        return m.group(1).strip()

    m = re.search(r"/\s*([^/]+?)\s*(ф-ра|$)", desc)
    if m:
        return m.group(1).strip()

    return ""


def extract_basis(desc):
    if "АТМ" in desc or "ATM" in desc:
        return "Теглене АТМ"

    m = re.search(r"ф-ра\s*([A-Za-z0-9]+)", desc)
    if m:
        return f"ф-ра {m.group(1)}"

    return ""


# ============================================================
# 3) Главен UniCredit парсер
# ============================================================

def parse_unicredit(pdf_bytes):
    rows = extract_table_rows(pdf_bytes)

    operations = []
    current = None

    for row in rows:
        texts = [c["text"] for c in row]

        # 1) Дата → начало на нова операция
        date = merge_date_cells(texts)
        if date:
            if current:
                operations.append(current)

            current = {
                "date": date,
                "description": "",
                "type": "",
                "eur": "",
                "transaction_id": ""
            }
            continue

        if not current:
            continue

        # 2) Описание
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

    if current:
        operations.append(current)

    # 6) Контрагент + основание
    for op in operations:
        op["description"] = op["description"].strip()
        op["counterparty"] = extract_counterparty(op["description"])
        op["basis"] = extract_basis(op["description"])

    return operations
