import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal
from statistics import median

DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
EUR_RE = re.compile(r"^\d{1,3}(?:[.,]\d{3})*[.,]\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9]{10,}$")

def cluster_x(coords):
    coords = sorted(coords)
    clusters = [[coords[0]]]
    for x in coords[1:]:
        if abs(x - clusters[-1][-1]) < 25:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    return [median(c) for c in clusters]

def extract_rows(pdf_bytes):
    path = "tmp_unicredit.pdf"
    with open(path, "wb") as f: f.write(pdf_bytes)
    items = []
    for page in extract_pages(path):
        for el in page:
            if isinstance(el, (LTTextBoxHorizontal, LTTextLineHorizontal)):
                t = el.get_text().strip()
                if t:
                    items.append((t, el.x0, el.y0))
    items.sort(key=lambda x: -x[2])
    rows, cur, last_y = [], [], None
    for t, x, y in items:
        if last_y is None or abs(y - last_y) < 3:
            cur.append((t, x))
            last_y = y
        else:
            rows.append(cur)
            cur = [(t, x)]
            last_y = y
    if cur: rows.append(cur)
    return rows

def detect_columns(rows):
    xs = []
    for r in rows:
        for t, x in r:
            if DATE_RE.search(t) or " / " in t:
                xs.append(x)
    return sorted(cluster_x(xs))[:6]

def normalize_date(texts):
    d = [t for t in texts if DATE_RE.search(t)]
    if not d: return ""
    return DATE_RE.search(d[0]).group(0)

def normalize_type(t):
    if "КТ" in t or "CT" in t: return "кредит"
    return "дебит"

def extract_counterparty(desc):
    if "ATM" in desc or "АТМ" in desc: return "UniCredit Bulbank"
    m = re.search(r"/\s*([A-Za-zА-Яа-я0-9 .\-]+)", desc)
    if m: return m.group(1).strip()
    m = re.search(r"Контрагент\s*:\s*([A-Za-zА-Яа-я0-9 .\-]+)", desc)
    if m: return m.group(1).strip()
    return ""

def extract_basis(desc):
    if "ATM" in desc or "АТМ" in desc: return "ATM"
    m = re.search(r"ф-ра\s*([A-Za-z0-9\-]+)", desc)
    if m: return f"ф-ра {m.group(1)}"
    if "заплата" in desc.lower(): return "заплата"
    if "такса" in desc.lower(): return "такса"
    return ""

def build_description(desc, eur, counterparty, basis):
    parts = []
    if "ATM" in desc or "АТМ" in desc:
        parts = ["ATM", counterparty, f"{eur} EUR"]
        return " | ".join([p for p in parts if p])
    if "SEPA" in desc or "SOUT" in desc:
        parts.append("SEPA")
    elif "вътр.банков" in desc or "вътр" in desc:
        parts.append("Вътрешнобанков")
    elif "междубанков" in desc:
        parts.append("Междубанков")
    if counterparty: parts.append(counterparty)
    m = re.search(r"(BG[0-9A-Z]{20,})", desc)
    if m: parts.append(m.group(1))
    if basis: parts.append(basis)
    return " | ".join(parts)

def parse_unicredit(pdf_bytes):
    rows = extract_rows(pdf_bytes)
    cols = detect_columns(rows)
    ops, cur = [], None

    for r in rows:
        r_sorted = sorted(r, key=lambda x: x[1])
        texts = [t for t, _ in r_sorted]
        xs = [x for _, x in r_sorted]

        date = normalize_date(texts)
        if date:
            if cur: ops.append(cur)
            cur = {"date": date, "desc": [], "type": "", "eur": "", "id": ""}
            continue

        if not cur: continue

        for t, x in r_sorted:
            if t.startswith("-"):
                cur["desc"].append(t)
            if "ДТ" in t or "КТ" in t or "DT" in t or "CT" in t:
                cur["type"] = normalize_type(t)
            if EUR_RE.match(t.replace(",", "")):
                cur["eur"] = t.replace(",", "")
            if ID_RE.match(t):
                cur["id"] = t

    if cur: ops.append(cur)

    final = []
    for o in ops:
        desc = " ".join(o["desc"])
        counterparty = extract_counterparty(desc)
        basis = extract_basis(desc)
        description = build_description(desc, o["eur"], counterparty, basis)
        final.append({
            "date": o["date"],
            "description": description,
            "type": o["type"],
            "eur": o["eur"],
            "transaction_id": o["id"],
            "counterparty": counterparty,
            "basis": basis
        })
    return final
