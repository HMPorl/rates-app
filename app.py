# net_rates_calculator_with_session_save.py

import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import json

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Net Rates Calculator", layout="wide")
st.title("Net Rates Calculator")

# -------------------------------
# File Uploads and Inputs
# -------------------------------
@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

# Initialize session state defaults
if "customer_name" not in st.session_state:
    st.session_state["customer_name"] = ""
if "global_discount" not in st.session_state:
    st.session_state["global_discount"] = 0.0

# Customer name input
customer_name = st.text_input("Enter Customer Name", value=st.session_state["customer_name"])
st.session_state["customer_name"] = customer_name

# Logo and file uploads
logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
uploaded_file = st.file_uploader("1 Upload your Excel file", type=["xlsx"])
header_pdf_file = st.file_uploader("Upload PDF Header (e.g., NRHeader.pdf)", type=["pdf"])

# -------------------------------
# Save or Load Session
# -------------------------------
st.markdown("## Save or Load Session")

# Define which keys to export
session_keys_to_export = [
    "customer_name",
    "global_discount"
]

# Dynamically include group-level discounts, custom prices, and transport charges
for key in st.session_state.keys():
    if key.endswith("_discount") or key.startswith("price_") or key.startswith("transport_"):
        session_keys_to_export.append(key)

# --- Export Section ---
st.markdown("### Export Session")
export_filename = st.text_input("Enter a name for your session file (without extension)", value="my_session")

if st.button("Export Session"):
    export_data = {key: st.session_state[key] for key in session_keys_to_export if key in st.session_state}
    export_json = json.dumps(export_data, indent=2)
    export_bytes = io.BytesIO(export_json.encode("utf-8"))
    st.download_button(
        label="Download Session File",
        data=export_bytes,
        file_name=f"{export_filename}.json",
        mime="application/json"
    )

# --- Import Section ---
st.markdown("### Import Session")
import_file = st.file_uploader("Upload a previously saved session file", type=["json"])

if import_file:
    try:
        imported_data = json.load(import_file)
        for key, value in imported_data.items():
            st.session_state[key] = value
        st.success("Session restored successfully! You may need to refresh the page to see all changes.")
    except Exception as e:
        st.error(f"Failed to load session: {e}")

# -------------------------------
# Load and Validate Excel File
# -------------------------------
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

    global_discount = st.number_input("Global Discount (%)", min_value=0.0, max_value=100.0, value=st.session_state["global_discount"], step=0.5)
    st.session_state["global_discount"] = global_discount

    st.markdown("### Group-Level Discounts")
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())
    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]
        key = f"{group}_{subsection}_discount"
        if key not in st.session_state:
            st.session_state[key] = global_discount
        with col:
            st.session_state[key] = st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state[key],
                step=0.5,
                key=key
            )

    def get_discounted_price(row):
        key = f"{row['GroupName']}_{row['Sub Section']}_discount"
        discount = st.session_state.get(key, global_discount)
        return row["HireRateWeekly"] * (1 - discount / 100)

    def calculate_discount_percent(original, custom):
        return ((original - custom) / original) * 100 if original else 0

    st.markdown("### Adjust Prices by Group and Sub Section")
    for (group, subsection), group_df in df.groupby(["GroupName", "Sub Section"]):
        with st.expander(f"{group} - {subsection}", expanded=False):
            for idx, row in group_df.iterrows():
                discounted_price = get_discounted_price(row)
                price_key = f"price_{idx}"
                if price_key not in st.session_state:
                    st.session_state[price_key] = ""

                col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 3, 3])
                with col1:
                    st.write(row["ItemCategory"])
                with col2:
                    st.write(row["EquipmentName"])
                with col3:
                    st.write(f"£{discounted_price:.2f}")
                with col4:
                    st.session_state[price_key] = st.text_input("", value=st.session_state[price_key], key=price_key, label_visibility="collapsed")
                with col5:
                    try:
                        custom_price = float(st.session_state[price_key]) if st.session_state[price_key] else discounted_price
                    except:
                        custom_price = discounted_price
                    discount_percent = calculate_discount_percent(row["HireRateWeekly"], custom_price)
                    st.markdown(f"**{discount_percent:.1f}%**")
                    if discount_percent > row["Max Discount"]:
                        st.warning(f"⚠️ Exceeds Max Discount ({row['Max Discount']}%)")

                df.at[idx, "CustomPrice"] = custom_price
                df.at[idx, "DiscountPercent"] = discount_percent

    st.markdown("### Final Price List")
    st.dataframe(df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly",
        "GroupName", "Sub Section", "CustomPrice", "DiscountPercent"
    ]], use_container_width=True)

    st.markdown("### Manually Entered Custom Prices")
    manual_entries = []
    for idx, row in df.iterrows():
        price_key = f"price_{idx}"
        user_input = st.session_state.get(price_key, "").strip()
        if user_input:
            try:
                entered_price = float(user_input)
                manual_entries.append({
                    "ItemCategory": row["ItemCategory"],
                    "EquipmentName": row["EquipmentName"],
                    "HireRateWeekly": row["HireRateWeekly"],
                    "CustomPrice": entered_price,
                    "DiscountPercent": calculate_discount_percent(row["HireRateWeekly"], entered_price),
                    "GroupName": row["GroupName"],
                    "Sub Section": row["Sub Section"]
                })
            except ValueError:
                continue

    if manual_entries:
        manual_df = pd.DataFrame(manual_entries)
        st.dataframe(manual_df, use_container_width=True)
    else:
        st.info("No manual custom prices have been entered.")

    st.markdown("### Transport Charges")
    transport_types = [
        "Standard - small tools", "Towables", "Non-mechanical", "Fencing",
        "Tower", "Powered Access", "Low-level Access", "Long Distance"
    ]
    default_charges = ["5", "7.5", "10", "15", "5", "Negotiable", "5", "15"]
    transport_inputs = []

    for i, (transport_type, default_value) in enumerate(zip(transport_types, default_charges)):
        key = f"transport_{i}"
        if key not in st.session_state:
            st.session_state[key] = default_value
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{transport_type}**")
        with col2:
            st.session_state[key] = st.text_input(
                f"Charge for {transport_type}",
                value=st.session_state[key],
                key=key,
                label_visibility="collapsed"
            )
            transport_inputs.append({
                "Delivery or Collection type": transport_type,
                "Charge (£)": st.session_state[key]
            })

    transport_df = pd.DataFrame(transport_inputs)
    st.markdown("### Transport Charges Summary")
    st.dataframe(transport_df, use_container_width=True)




