import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# Set page config
st.set_page_config(page_title="Net Rates Calculator", layout="wide")

st.title("Net Rates Calculator")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName"}
    if not required_columns.issubset(df.columns):
        st.error(f"Excel file must contain the following columns: {', '.join(required_columns)}")
        st.stop()

    # Add a column for custom prices
    if "CustomPrice" not in df.columns:
        df["CustomPrice"] = df["HireRateWeekly"]

    # Global discount
    discount = st.slider("Global Discount (%)", min_value=0, max_value=100, value=0)
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
                new_price = st.number_input(
                    f"Custom price for {row['ItemCategory']}",
                    min_value=0.0,
                    value=float(row["DiscountedPrice"]),
                    key=f"price_{idx}"
                )
                final_df.at[idx, "CustomPrice"] = new_price

    st.markdown("### Final Price List")
    st.dataframe(final_df[["ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName", "CustomPrice"]])

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

    table_data = [["ItemCategory", "EquipmentName", "HireRateWeekly", "CustomPrice"]]
    for _, row in group_df.iterrows():
        table_data.append([
            row["ItemCategory"],
            row["EquipmentName"],
            f"£{row['HireRateWeekly']:.2f}",
            f"£{row['CustomPrice']:.2f}"
        ])

    table = Table(table_data, colWidths=[100, 150, 100, 100])
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


    st.download_button(
        label="Download as PDF",
        data=pdf_buffer,
        file_name="custom_price_list.pdf",
        mime="application/pdf"
    )
else:
    st.info("Please upload an Excel file to begin.")

