import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(page_title="Net Rates Calculator", layout="wide")
st.title("Net Rates Calculator")

if st.button("🔄 Clear All Inputs"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    try:
        st.experimental_rerun()
    except Exception:
        st.warning("Please manually refresh the page to complete reset.")

@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

customer_name = st.text_input("Enter Customer Name")
logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
uploaded_file = st.file_uploader("1 Upload your Excel file", type=["xlsx"])
header_pdf_file = st.file_uploader("Upload PDF Header (e.g., NRHeader.pdf)", type=["pdf"])

if uploaded_file and header_pdf_file:
    try:
        df = load_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName", "Sub Section", "Max Discount", "Include", "Order"}
    if not required_columns.issubset(df.columns):
        st.error(f"Excel file must contain the following columns: {', '.join(required_columns)}")
        st.stop()

    df = df[df["Include"] == True].copy()
    df.sort_values(by=["GroupName", "Sub Section", "Order"], inplace=True)

    global_discount = st.number_input("Global Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

    st.markdown("### Group-Level Discounts")
    group_discount_keys = {}
    for (group, subsection), _ in df.groupby(["GroupName", "Sub Section"]):
        key = f"{group}_{subsection}_discount"
        group_discount_keys[(group, subsection)] = key
        st.number_input(
            f"Discount for {group} - {subsection} (%)",
            min_value=0.0,
            max_value=100.0,
            value=global_discount,
            step=0.5,
            key=key
        )

    st.markdown("### Adjust Prices by Group and Sub Section")
    for (group, subsection), group_df in df.groupby(["GroupName", "Sub Section"]):
        with st.expander(f"{group} - {subsection}", expanded=False):
            for idx, row in group_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 4, 3, 3])
                with col1:
                    st.write(row["ItemCategory"])
                with col2:
                    st.write(row["EquipmentName"])
                with col3:
                    discount_key = group_discount_keys.get((row["GroupName"], row["Sub Section"]))
                    group_discount = st.session_state.get(discount_key, global_discount)
                    discounted_price = row["HireRateWeekly"] * (1 - group_discount / 100)
                    price_key = f"price_{idx}"
                    default_price = st.session_state.get(price_key, f"{discounted_price:.2f}")
                    st.text_input(
                        "",
                        value=default_price,
                        key=price_key,
                        label_visibility="collapsed"
                    )
                with col4:
                    try:
                        custom_price = float(st.session_state[price_key])
                    except:
                        custom_price = row["HireRateWeekly"]
                    discount_percent = ((row["HireRateWeekly"] - custom_price) / row["HireRateWeekly"]) * 100
                    st.markdown(f"**Discount: {discount_percent:.1f}%**")

    for idx in df.index:
        price_key = f"price_{idx}"
        try:
            df.at[idx, "CustomPrice"] = float(st.session_state[price_key])
        except:
            df.at[idx, "CustomPrice"] = df.at[idx, "HireRateWeekly"]

    df["DiscountPercent"] = ((df["HireRateWeekly"] - df["CustomPrice"]) / df["HireRateWeekly"]) * 100

    st.markdown("### Final Price List")
    st.dataframe(df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly",
        "GroupName", "Sub Section", "CustomPrice", "DiscountPercent"
    ]], use_container_width=True)












































    

















    
