import streamlit as st
import pandas as pd
from unicredit_parser import parse_unicredit

st.set_page_config(page_title="UniCredit PDF Parser", layout="wide")

st.title("UniCredit PDF Parser")

uploaded = st.file_uploader("Качи UniCredit PDF", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()

    with st.spinner("Обработка на PDF..."):
        operations = parse_unicredit(pdf_bytes)

    df = pd.DataFrame(operations)

    st.subheader("Извлечени операции")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Свали CSV", csv, "unicredit_export.csv", "text/csv")
