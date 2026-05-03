import streamlit as st
import pandas as pd
from unicredit_parser import extract_unicredit_text, parse_unicredit_transactions

st.title("UniCredit PDF Parser")

uploaded_file = st.file_uploader("Качи UniCredit PDF", type=["pdf"])

if uploaded_file:
    text = extract_unicredit_text(uploaded_file.read())
    data = parse_unicredit_transactions(text)
    df = pd.DataFrame(data)
    st.data_editor(df, use_container_width=True)
