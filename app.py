import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

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

    # Export to PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    x_margin = 50
    y = height - 50
    line_height = 14

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_margin, y, "Custom Price List")
    y -= 30

    c.setFont("Helvetica", 10)
    for group, group_df in final_df.groupby("GroupName"):
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_margin, y, f"Group: {group}")
        y -= 20
        c.setFont("Helvetica", 10)
        for _, row in group_df.iterrows():
            line = f"{row['ItemCategory']} - {row['EquipmentName']} | Weekly Rate: £{row['HireRateWeekly']:.2f} | Custom Price: £{row['CustomPrice']:.2f}"
            c.drawString(x_margin, y, line)
            y -= line_height
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)

    c.save()
    pdf_buffer.seek(0)

    st.download_button(
        label="Download as PDF",
        data=pdf_buffer,
        file_name="custom_price_list.pdf",
        mime="application/pdf"
    )
else:
    st.info("Please upload an Excel file to begin.")

