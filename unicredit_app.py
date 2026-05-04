from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal
import re


def extract_layout_rows(pdf_bytes):
    """
    Връща списък от редове, където всеки ред е списък от клетки:
    [
        {"text": "...", "x0": ..., "y0": ..., "x1": ..., "y1": ...},
        ...
    ]
    """

    temp_path = "unicredit_temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)

    elements = []

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

    # групиране по редове чрез y0
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

    # сортиране по x0 вътре в реда
    sorted_rows = []
    for row in rows:
        sorted_rows.append(sorted(row, key=lambda e: e["x0"]))

    return sorted_rows
