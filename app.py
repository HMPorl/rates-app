import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Set page config
st.set_page_config(page_title="Net Rates Calculator", layout="wide")

st.title("Net Rates Calculator V1")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
header_pdf_file = st.file_uploader("Upload PDF Header (e.g., NRHeader.pdf)", type=["pdf"])

if uploaded_file and header_pdf_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName"}
    if not required_columns.issubset(df.columns):
        st.error(f"Excel file must contain the following columns: {', '.join(required_columns)}")
        st.stop()

    # Add a column for custom prices if not already present
    if "CustomPrice" not in df.columns:
        df["CustomPrice"] = df["HireRateWeekly"]

    # Global discount using text input
    discount_input = st.text_input("Global Discount (%)", value="0")
    try:
        discount = float(discount_input)
        if not (0 <= discount <= 100):
            st.warning("Please enter a discount between 0 and 100.")
            st.stop()
    except ValueError:
        st.warning("Please enter a valid number for the discount.")
        st.stop()

    # Apply global discount
    df["DiscountedPrice"] = df["HireRateWeekly"] * (1 - discount / 100)

    st.markdown("### Adjust Prices by Group")

    # Create a copy to store final prices
    final_df = df.copy()

    # Group by GroupName
    grouped = df.groupby("GroupName")

    for group, group_df in grouped:
        st.subheader(group)
        for idx, row in group_df.iterrows():
            col1, col2, col3 = st.columns([2, 4, 4])
            with col1:
                st.text(row["ItemCategory"])
            with col2:
                st.text(row["EquipmentName"])
            with col3:
                default_price = float(row["CustomPrice"]) if row["CustomPrice"] != row["HireRateWeekly"] else float(row["DiscountedPrice"])
                new_price = st.number_input(
                    f"Custom price for {row['ItemCategory']}",
                    min_value=0.0,
                    value=default_price,
                    key=f"price_{idx}"
                )
                final_df.at[idx, "CustomPrice"] = new_price

    # Calculate DiscountPercent
    final_df["DiscountPercent"] = ((final_df["HireRateWeekly"] - final_df["CustomPrice"]) / final_df["HireRateWeekly"]) * 100
    st.markdown("### Final Price List")
    st.dataframe(final_df[["ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName", "CustomPrice", "DiscountPercent"]])

    # Export to Excel
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False)
    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Export to PDF with table formatting
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Custom Price List", styles['Title']))
    elements.append(Spacer(1, 12))

    for group, group_df in final_df.groupby("GroupName"):
        elements.append(Paragraph(f"Group: {group}", styles['Heading2']))
        elements.append(Spacer(1, 6))

        table_data = [["ItemCategory", "EquipmentName", "CustomPrice", "DiscountPercent"]]
        for _, row in group_df.iterrows():
            table_data.append([
                row["ItemCategory"],
                Paragraph(row["EquipmentName"], styles['BodyText']),
                f"£{row['CustomPrice']:.2f}",
                f"{row['DiscountPercent']:.1f}%"
            ])

        table = Table(table_data, colWidths=[100, 200, 80, 80])
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

    doc.build(elements)
    pdf_buffer.seek(0)

    # Merge header PDF with generated PDF
    merged_pdf = fitz.open(stream=header_pdf_file.read(), filetype="pdf")
    generated_pdf = fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf")
    for page in generated_pdf:
        merged_pdf.insert_pdf(generated_pdf, from_page=page.number, to_page=page.number)
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



    