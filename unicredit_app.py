import streamlit as st
import re
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams # Важно за NameError

# 1. Първо дефинираме функцията
def extract_unicredit_text(pdf_bytes):
    # Използваме LAParams, за да запазим структурата на колоните
    params = LAParams(
        line_overlap=0.5,
        char_margin=2.0,
        line_margin=0.5,
        word_margin=0.1,
        boxes_flow=0.5,
        detect_vertical=True
    )
    return extract_text(BytesIO(pdf_bytes), laparams=params)

# 2. След това е логиката на Streamlit
uploaded_file = st.file_uploader("Качете PDF", type="pdf")

if uploaded_file is not None:
    # Четем съдържанието
    file_content = uploaded_file.read()
    
    # Сега вече можем да извикаме функцията без грешка
    try:
        text = extract_unicredit_text(file_content)
        st.success("Текстът е извлечен успешно!")
        
        # Показваме малка част за проверка
        with st.expander("Виж суров текст"):
            st.text(text[:2000])
            
    except Exception as e:
        st.error(f"Грешка при обработката: {e}")
