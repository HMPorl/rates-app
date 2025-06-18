import streamlit as st
import pandas as pd
import io
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import fitz  # PyMuPDF

# --- Streamlit Page Config and CSS ---
st.set_page_config(page_title="Net Rates Calculator", layout="wide")
st.title("Net Rates Calculator")

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
        background-color: #ffb347 !important; /* orange */
        color: #222 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Caching Functions ---
@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

# --- User Inputs ---
customer_name = st.text_input("Enter Customer Name")
logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
uploaded_file = st.file_uploader("1 Upload your Excel file", type=["xlsx"])
header_pdf_file = st.file_uploader("Upload PDF Header (e.g., NRHeader.pdf)", type=["pdf"])

# --- Main Logic ---
if uploaded_file and header_pdf_file:
    try:
        df = load_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()

    required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName", "Sub Section", "Max Discount", "Include", "Order"}
    if not required_columns.issubset(df.columns):
        st.error(f"Excel file must contain columns: {required_columns}")
        st.stop()

    df = df[df["Include"] == True].copy()
    df.sort_values(by=["GroupName", "Sub Section", "Order"], inplace=True)

    if "CustomPrice" not in df.columns:
        df["CustomPrice"] = df["HireRateWeekly"]

    discount_input = st.text_input("Global Discount (%)", value="0")
    try:
        discount = float(discount_input)
    except ValueError:
        st.error("Please enter a valid number for discount.")
        st.stop()

    df["DiscountedPrice"] = df["HireRateWeekly"] * (1 - discount / 100)
    final_df = df.copy()

    st.markdown("### Adjust Prices by Group and Sub Section")

    # Allow per-group/subsection custom price entry
    for (group, subsection), group_df in df.groupby(["GroupName", "Sub Section"]):
        st.markdown(f"**{group} / {subsection}**")
        for idx, row in group_df.iterrows():
            custom_price = st.number_input(
                f"Custom price for {row['EquipmentName']} (was £{row['HireRateWeekly']:.2f})",
                min_value=0.0,
                value=float(row["CustomPrice"]),
                key=f"custom_{idx}"
            )
            final_df.at[idx, "CustomPrice"] = custom_price

    final_df["DiscountPercent"] = ((final_df["HireRateWeekly"] - final_df["CustomPrice"]) / final_df["HireRateWeekly"]) * 100

    st.markdown("### Final Price List")

    def highlight_special_rates(row):
        # Highlight GroupName and Sub Section in orange if any custom price in subsection
        custom_subsections = set(
            final_df.loc[
                final_df["CustomPrice"].round(2) != final_df["DiscountedPrice"].round(2),
                ["GroupName", "Sub Section"]
            ].apply(tuple, axis=1)
        )
        if (row["GroupName"], row["Sub Section"]) in custom_subsections:
            return [
                'background-color: orange' if col in ['GroupName', 'Sub Section'] else ''
                for col in row.index
            ]
        if round(row["CustomPrice"], 2) != round(row["DiscountedPrice"], 2):
            return [
                'background-color: yellow' if col == 'GroupName' else ''
                for col in row.index
            ]
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

    # --- Excel Export ---
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False, sheet_name="Price List")
        manual_updates_df.to_excel(writer, index=False, sheet_name="Manual Updates")
        edited_transport_df.to_excel(writer, index=False, sheet_name="Transport Charges")
    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- PDF Export ---
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Page 1: Title
    elements.append(Paragraph("Custom Price List", styles['Title']))
    elements.append(Spacer(1, 12))

    # Page 1-2: Price List by Group/Subsection
    for (group, subsection), group_df in final_df.groupby(["GroupName", "Sub Section"]):
        elements.append(Paragraph(f"{group} / {subsection}", styles['Heading2']))
        table_data = [["ItemCategory", "EquipmentName", "HireRateWeekly", "CustomPrice", "DiscountPercent", "DiscountedPrice"]]
        for _, row in group_df.iterrows():
            table_data.append([
                row["ItemCategory"],
                row["EquipmentName"],
                f"£{row['HireRateWeekly']:.2f}",
                f"£{row['CustomPrice']:.2f}",
                f"{row['DiscountPercent']:.1f}%",
                f"£{row['DiscountedPrice']:.2f}"
            ])
        t = Table(table_data, colWidths=[70, 120, 70, 70, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    # Page 2: Summary of Manually Updated Prices
    if not manual_updates_df.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("Summary of Manually Updated Prices", styles['Heading2']))
        summary_data = [["ItemCategory", "EquipmentName", "GroupName", "Sub Section", "HireRateWeekly", "CustomPrice"]]
        for _, row in manual_updates_df.iterrows():
            summary_data.append([
                row["ItemCategory"],
                row["EquipmentName"],
                row["GroupName"],
                row["Sub Section"],
                f"£{row['HireRateWeekly']:.2f}",
                f"£{row['CustomPrice']:.2f}"
            ])
        t2 = Table(summary_data, colWidths=[70, 120, 70, 70, 70, 70])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 12))

    # Page 3: Transport Charges Table
    elements.append(PageBreak())
    elements.append(Paragraph("Transport Charges", styles['Heading2']))
    elements.append(Spacer(1, 12))
    transport_pdf_data = [["Delivery or Collection type", "Charge (£)"]]
    for idx, row in edited_transport_df.iterrows():
        transport_pdf_data.append([row["Delivery or Collection type"], row["Charge (£)"]])
    transport_table = Table(transport_pdf_data, colWidths=[250, 100])
    transport_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(transport_table)

    doc.build(elements)
    pdf_buffer.seek(0)

    # --- Modify header PDF with customer name and logo ---
    header_data = read_pdf_header(header_pdf_file)
    header_pdf = fitz.open(stream=header_data, filetype="pdf")
    page = header_pdf[0]

    if customer_name:
        # Add customer name to header PDF (simple text overlay)
        rect = fitz.Rect(50, 50, 400, 100)
        page.insert_textbox(rect, customer_name, fontsize=18, color=(0, 0, 0))

    if logo_file:
        # Add logo to header PDF
        logo_img = Image.open(logo_file)
        img_bytes = io.BytesIO()
        logo_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        page.insert_image(fitz.Rect(450, 30, 550, 130), stream=img_bytes.getvalue())

    modified_header = io.BytesIO()
    header_pdf.save(modified_header)
    header_pdf.close()

    merged_pdf = fitz.open(stream=modified_header.getvalue(), filetype="pdf")
    generated_pdf = fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf")
    merged_pdf.insert_pdf(generated_pdf)
    merged_output = io.BytesIO()
    merged_pdf.save(merged_output)
    merged_pdf.close()

    st.download_button(
        label="Download as PDF",
        data=merged_output.getvalue(),
        file_name="custom_price_list.pdf",
        mime="application/pdf"
    )
else:
    st.info("Please upload both an Excel file and a header PDF to begin.")






