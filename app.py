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
# Save or Load Session Section
# -------------------------------
st.markdown("## 💾 Save or Load Session")

# Export
export_filename = st.text_input("Enter a name for your session file (without extension)", value="my_session")

if st.button("📤 Export Session"):
    session_keys_to_export = [
        "customer_name",
        "global_discount"
    ]
    for key in st.session_state.keys():
        if key.endswith("_discount") or key.startswith("price_") or key.startswith("transport_"):
            session_keys_to_export.append(key)
    export_data = {key: st.session_state[key] for key in session_keys_to_export if key in st.session_state}
    export_json = json.dumps(export_data, indent=2)
    export_bytes = io.BytesIO(export_json.encode("utf-8"))
    st.download_button(
        label="Download Session File",
        data=export_bytes,
        file_name=f"{export_filename}.json",
        mime="application/json"
    )

# Import
import_file = st.file_uploader("📥 Upload a previously saved session file", type=["json"], key="import_json")
if import_file:
    try:
        imported_data = json.load(import_file)
        for key, value in imported_data.items():
            st.session_state[key] = value
        st.success("Session restored successfully! You may need to refresh the page to see all changes.")
    except Exception as e:
        st.error(f"Failed to load session: {e}")

# -------------------------------
# File Uploads and Inputs
# -------------------------------
@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

customer_name = st.text_input("Enter Customer Name", value=st.session_state.get("customer_name", ""))
st.session_state["customer_name"] = customer_name

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

    global_discount = st.number_input("Global Discount (%)", min_value=0.0, max_value=100.0, value=st.session_state.get("global_discount", 0.0), step=0.5)
    st.session_state["global_discount"] = global_discount

    st.markdown("### Group-Level Discounts")
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())
    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]
        key = f"{group}_{subsection}_discount"
        with col:
            val = st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.get(key, global_discount),
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
                default_val = st.session_state.get(price_key, "")
                col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 3, 3])
                with col1:
                    st.write(row["ItemCategory"])
                with col2:
                    st.write(row["EquipmentName"])
                with col3:
                    st.write(f"£{discounted_price:.2f}")
                with col4:
                    user_input = st.text_input("", value=default_val, key=price_key, label_visibility="collapsed")
                with col5:
                    try:
                        custom_price = float(user_input) if user_input else discounted_price
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
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{transport_type}**")
        with col2:
            charge = st.text_input(
                f"Charge for {transport_type}",
                value=st.session_state.get(f"transport_{i}", default_value),
                key=f"transport_{i}",
                label_visibility="collapsed"
            )
            transport_inputs.append({
                "Delivery or Collection type": transport_type,
                "Charge (£)": charge
            })

    transport_df = pd.DataFrame(transport_inputs)
    st.markdown("### Transport Charges Summary")
    st.dataframe(transport_df, use_container_width=True)

    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




