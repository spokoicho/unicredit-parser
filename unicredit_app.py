import streamlit as st
import re
import pandas as pd
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams  # <--- ТОВА ЛИПСВАШЕ
from datetime import datetime

st.title("UniCredit PDF Parser")

uploaded_file = st.file_uploader("Качи UniCredit PDF", type=["pdf"])

if uploaded_file:
    text = extract_unicredit_text(uploaded_file.read())
    data = parse_unicredit_transactions(text)
    df = pd.DataFrame(data)
    st.data_editor(df, use_container_width=True)
