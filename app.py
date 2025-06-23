
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

# Clear session state button
if st.button("🔄 Clear All Inputs"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

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
        if key not in st.session_state:
            st.session_state[key] = global_discount
        st.number_input(
            f"Discount for {group} - {subsection} (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state[key],
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

    st.markdown("### Transport Charges")
    transport_types = [
        "Standard - small tools", "Towables", "Non-mechanical", "Fencing",
        "Tower", "Powered Access", "Low-level Access", "Long Distance"
    ]
    transport_data = {
        "Delivery or Collection type": transport_types,
        "Charge (£)": ["Negotiable" if t == "Powered Access" else "" for t in transport_types]
    }
    transport_df = pd.DataFrame(transport_data)
    powered_access_idx = transport_types.index("Powered Access")

    edited_transport_df = st.data_editor(
        transport_df,
        column_config={
            "Charge (£)": st.column_config.TextColumn("Charge (£)", help="Enter charge in £")
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
        df.to_excel(writer, index=False)
    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Custom Price List", styles['Title']))
    elements.append(Spacer(1, 12))

    for (group, subsection), group_df in df.groupby(["GroupName", "Sub Section"]):
        elements.append(Paragraph(f"Group: {group} - Sub Section: {subsection}", styles['Heading2']))
        elements.append(Spacer(1, 6))
        table_data = [["Category", "Equipment", "Price (£)", "Discount (%)"]]
        for _, row in group_df.iterrows():
            table_data.append([
                row["ItemCategory"],
                Paragraph(row["EquipmentName"], styles['BodyText']),
                f"£{row['CustomPrice']:.2f}",
                f"{row['DiscountPercent']:.1f}%"
            ])
        table = Table(table_data, colWidths=[100, 200, 80, 80], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

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

    header_data = read_pdf_header(header_pdf_file)
    header_pdf = fitz.open(stream=header_data, filetype="pdf")
    page = header_pdf[0]

    if customer_name:
        font_size = 22
        font_color = (0 / 255, 45 / 255, 86 / 255)
        font_name = "helv"
        page_width = page.rect.width
        page_height = page.rect.height
        text_y = page_height / 3
        font = fitz.Font(fontname=font_name)
        text_width = font.text_length(customer_name, fontsize=font_size)
        text_x = (page_width - text_width) / 2
        page.insert_text((text_x, text_y), customer_name, fontsize=font_size, fontname=font_name, fill=font_color)

        if logo_file:
            logo_image = Image.open(logo_file)
            logo_bytes = io.BytesIO()
            logo_image.save(logo_bytes, format="PNG")
            logo_bytes.seek(0)
            logo_width = 100
            logo_height = logo_image.height * (logo_width / logo_image.width)
            logo_x = (page_width - logo_width) / 2
            logo_y = text_y + font_size + 20
            rect_logo = fitz.Rect(logo_x, logo_y, logo_x + logo_width, logo_y + logo_height)
            page.insert_image(rect_logo, stream=logo_bytes.read())

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












































    

















    
