# Rewriting the Streamlit script with corrected indentation and including the new section for manually updated prices and transport charges

import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ✅ Set page config
st.set_page_config(page_title="Net Rates Calculator", layout="wide")
st.title("Net Rates Calculator")

# ✅ Custom CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    .stTextInput input {
        height: 28px;
    }
    .stTextInput {
        margin-bottom: 0.25rem;
    }
    thead tr th:hover {
        background-color: #ffb347 !important;
        color: #222 !important;
    }
    </style>    
""", unsafe_allow_html=True)

# ✅ Caching functions
@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

# ✅ Upload files and inputs
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

    if "CustomPrice" not in df.columns:
        df["CustomPrice"] = df["HireRateWeekly"]

    discount_input = st.text_input("Global Discount (%)", value="0")
    try:
        discount = float(discount_input)
        if not (0 <= discount <= 100):
            st.warning("Please enter a discount between 0 and 100.")
            st.stop()
    except ValueError:
        st.warning("Please enter a valid number for the discount.")
        st.stop()

    df["DiscountedPrice"] = df["HireRateWeekly"] * (1 - discount / 100)
    final_df = df.copy()

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
                    default_price = float(row["CustomPrice"]) if row["CustomPrice"] != row["HireRateWeekly"] else float(row["DiscountedPrice"])
                    price_input = st.text_input(
                        "",
                        value=f"{default_price:.2f}",
                        key=f"price_{idx}",
                        label_visibility="collapsed"
                    )
                    try:
                        new_price = float(price_input)
                        final_df.at[idx, "CustomPrice"] = new_price
                    except ValueError:
                        st.warning(f"Invalid price entered for {row['ItemCategory']}. Using default.")
                        final_df.at[idx, "CustomPrice"] = default_price
                with col4:
                    try:
                        discount_percent = ((row["HireRateWeekly"] - final_df.at[idx, "CustomPrice"]) / row["HireRateWeekly"]) * 100
                        st.write(f"{discount_percent:.1f}%")
                        if discount_percent > row["Max Discount"]:
                            st.warning(f"⚠️ {row['ItemCategory']} exceeds Max Discount ({row['Max Discount']}%)")
                    except ZeroDivisionError:
                        st.write("N/A")

    final_df["DiscountPercent"] = ((final_df["HireRateWeekly"] - final_df["CustomPrice"]) / final_df["HireRateWeekly"]) * 100

    st.markdown("### Final Price List")

    def highlight_special_rates(row):
        if round(row["CustomPrice"], 2) != round(row["DiscountedPrice"], 2):
            return ['background-color: yellow' if col == 'GroupName' else '' for col in row.index]
        else:
            return ['' for _ in row]

    styled_df = final_df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly",
        "GroupName", "Sub Section", "CustomPrice", "DiscountPercent", "DiscountedPrice"
    ]].style.apply(highlight_special_rates, axis=1)

    st.dataframe(styled_df, use_container_width=True)

    manual_updates_df = final_df[final_df["CustomPrice"].round(2) != final_df["DiscountedPrice"].round(2)]

    if not manual_updates_df.empty:
        st.markdown("### Summary of Manually Updated Prices")
        st.dataframe(manual_updates_df[[
            "ItemCategory", "EquipmentName", "GroupName", "Sub Section", "HireRateWeekly", "CustomPrice"
        ]], use_container_width=True)

    # --- Transport Charges Table ---
    st.markdown("### Transport Charges")

    transport_types = [
        "Standard - small tools",
        "Towables",
        "Non-mechanical",
        "Fencing",
        "Tower",
        "Powered Access",
        "Low-level Access",
        "Long Distance"
    ]

    transport_data = {
        "Delivery or Collection type": transport_types,
        "Charge (£)": [""] * len(transport_types)
    }
    powered_access_idx = transport_types.index("Powered Access")
    transport_data["Charge (£)"][powered_access_idx] = "Negotiable"

    transport_df = pd.DataFrame(transport_data)

    edited_transport_df = st.data_editor(
        transport_df,
        column_config={
            "Charge (£)": st.column_config.TextColumn(
                "Charge (£)",
                help="Enter charge in £ (leave as 'Negotiable' for Powered Access)"
            )
        },
        disabled={
            "Delivery or Collection type": True,
            "Charge (£)": [i == powered_access_idx for i in range(len(transport_types))]
        },
        hide_index=True,
        use_container_width=True
    )

    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False)

    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload both an Excel file and a header PDF to begin.")



















    

















    
