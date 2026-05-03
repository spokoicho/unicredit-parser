import streamlit as st
import pandas as pd
from unicredit_parser import extract_unicredit_text, parse_unicredit_transactions

st.set_page_config(page_title="UniCredit Parser", layout="wide")

st.title("📄 UniCredit PDF → Transactions Parser")

uploaded_file = st.file_uploader("Качи UniCredit PDF файл", type=["pdf"])

if uploaded_file:
    st.info("Извличане на текст от UniCredit PDF…")

    pdf_bytes = uploaded_file.read()
    text = extract_unicredit_text(pdf_bytes)

    st.subheader("📌 Извлечен текст (debug):")
    st.text_area("PDF Text", text, height=300)

    # Parse transactions
    transactions = parse_unicredit_transactions(text)

    if not transactions:
        st.error("❌ Не са открити транзакции в PDF файла.")
        st.stop()

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    st.subheader("📊 Транзакции (редактируеми)")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=600
    )

    st.success("Транзакциите са заредени и могат да се редактират.")

    # Show final edited data
    st.subheader("📤 Актуализирани данни")
    st.dataframe(edited_df, use_container_width=True)

    # Download edited data as CSV
    st.download_button(
        label="⬇️ Свали редактираните транзакции (CSV)",
        data=edited_df.to_csv(index=False),
        file_name="unicredit_transactions.csv",
        mime="text/csv"
    )
