# net_rates_calculator_group_discount_SaveFunc 34.py

import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import json
import os
import datetime
import requests
from datetime import datetime
import glob
from reportlab.lib.utils import ImageReader

def add_footer_logo(canvas, doc):
    logo_path = "HMChev.png"  # Place your logo in the app root folder
    page_width = doc.pagesize[0]
    # Stretch logo to full page width, minus small margins
    margin = 20  # points, adjust as needed
    logo_width = page_width - 2 * margin
    logo_height = 30  # or set to any desired height

    x = margin
    y = 10  # 10 points from the bottom

    try:
        canvas.drawImage(
            ImageReader(logo_path),
            x, y,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )
    except Exception:
        pass  # If logo not found, skip

# --- Weather: Current + Daily Summary ---
def get_weather_and_forecast(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=temperature_2m,weathercode"
        f"&timezone=Europe/London"
    )
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data["current_weather"]
        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        codes = data["hourly"]["weathercode"]
        return current, times, temps, codes
    except Exception:
        return None, [], [], []

city = "London"
lat, lon = 51.5074, -0.1278

current, times, temps, codes = get_weather_and_forecast(lat, lon)

weather_icons = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌦️", 56: "🌧️", 57: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️", 66: "🌧️", 67: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "🌨️", 77: "🌨️", 80: "🌦️",
    81: "🌦️", 82: "🌦️", 85: "🌨️", 86: "🌨️", 95: "⛈️",
    96: "⛈️", 99: "⛈️"
}

if current:
    # Current weather
    icon = weather_icons.get(current["weathercode"], "❓")
    st.markdown(
        f"### {icon} {city}: {current['temperature']}°C, Wind {current['windspeed']} km/h"
    )

    # Daily summary
    today = datetime.now().strftime("%Y-%m-%d")
    today_temps = [t for t, time in zip(temps, times) if time.startswith(today)]
    today_codes = [c for c, time in zip(codes, times) if time.startswith(today)]
    if today_temps:
        min_temp = min(today_temps)
        max_temp = max(today_temps)
        # Most common weather code for the day
        from collections import Counter
        main_code = Counter(today_codes).most_common(1)[0][0]
        main_icon = weather_icons.get(main_code, "❓")
        st.markdown(
            f"**Day: {main_icon} {min_temp:.1f}°C to {max_temp:.1f}°C**"
        )
else:
    st.markdown("### 🌦️ Weather: Unable to fetch data")



# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Net Rates Calculator", layout="wide")
st.title("Net Rates Calculator")

#if st.button("📂 Go to Load Progress Section"):
#    st.session_state["scroll_to_load"] = True

# Ensure progress_saves folder exists
if not os.path.exists("progress_saves"):
    os.makedirs("progress_saves")


# -------------------------------
# File Uploads and Inputs
# -------------------------------
DEFAULT_EXCEL_PATH = "Net rates Webapp.xlsx"  # Change this to your actual default file name

@st.cache_data
def load_excel(file):
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

customer_name = st.text_input("⭐Enter Customer Name")
bespoke_email = st.text_input("✉️ Bespoke email address (optional)")
logo_file = st.file_uploader("🖼️Upload Company Logo", type=["png", "jpg", "jpeg"])
uploaded_file = st.file_uploader("💹Upload your Excel file (Admin Only❗)", type=["xlsx"])
header_pdf_choice = st.selectbox(
    "Choose a PDF Header Sheet from the app folder, or upload your own:",
    ["(Upload a PDF header below)"] + glob.glob("*.pdf")
)
uploaded_header_pdf = st.file_uploader("Or upload a PDF Header (overrides selection above)", type=["pdf"], key="header_pdf_upload")

# -------------------------------
# Load and Validate Excel File
# -------------------------------
df = None
excel_source = None

if uploaded_file:
    try:
        df = load_excel(uploaded_file)
        excel_source = "uploaded"
        st.success("Excel file uploaded and loaded.")
    except Exception as e:
        st.error(f"Error reading uploaded Excel file: {e}")
        st.stop()
elif os.path.exists(DEFAULT_EXCEL_PATH):
    try:
        df = load_excel(DEFAULT_EXCEL_PATH)
        excel_source = "default"
        st.info(f"Loaded default Excel data from {DEFAULT_EXCEL_PATH}")
    except Exception as e:
        st.error(f"Failed to load default Excel: {e}")
        st.stop()

header_pdf_file = None
if uploaded_header_pdf is not None:
    # Use uploaded file (takes priority)
    header_pdf_file = uploaded_header_pdf
elif header_pdf_choice != "(Upload a PDF header below)":
    # Use selected file from folder
    with open(header_pdf_choice, "rb") as f:
        header_pdf_file = io.BytesIO(f.read())

if df is not None and header_pdf_file:
    required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", "GroupName", "Sub Section", "Max Discount", "Include", "Order"}
    if not required_columns.issubset(df.columns):
        st.error(f"Excel file must contain the following columns: {', '.join(required_columns)}")
        st.stop()

    # -------------------------------
    # Filter and Sort Data
    # -------------------------------
    df = df[df["Include"] == True].copy()
    df.sort_values(by=["GroupName", "Sub Section", "Order"], inplace=True)

    # -------------------------------
    # Global and Group-Level Discounts
    # -------------------------------
    global_discount = st.number_input("Global Discount (%)", min_value=0, max_value=100, value=0, step=1)

    st.markdown("### Group-Level Discounts")
    group_discount_keys = {}
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())

    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]  # Fill down each column
        with col:
            st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0,
                max_value=100,
                value=global_discount,
                step=1,
                key=f"{group}_{subsection}_discount"
            )


    # -------------------------------
    # Helper Functions
    # -------------------------------
    def get_discounted_price(row):
        key = f"{row['GroupName']}_{row['Sub Section']}_discount"
        discount = st.session_state.get(key, global_discount)
        return row["HireRateWeekly"] * (1 - discount / 100)

    def calculate_discount_percent(original, custom):
        return ((original - custom) / original) * 100 if original else 0

    # -------------------------------
    # Adjust Prices by Group and Sub Section
    # -------------------------------
    st.markdown("### Adjust Prices by Group and Sub Section")
    for (group, subsection), group_df in df.groupby(["GroupName", "Sub Section"]):
        with st.expander(f"{group} - {subsection}", expanded=False):
            for idx, row in group_df.iterrows():
                discounted_price = get_discounted_price(row)
                price_key = f"price_{idx}"

                col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 3, 3])
                with col1:
                    st.write(row["ItemCategory"])
                with col2:
                    st.write(row["EquipmentName"])
                with col3:
                    st.write(f"£{discounted_price:.2f}")
                with col4:
                    st.text_input("", key=price_key, label_visibility="collapsed")
                with col5:
                    try:
                        custom_price = float(st.session_state[price_key]) if st.session_state[price_key] else discounted_price
                    except:
                        custom_price = discounted_price
                    discount_percent = calculate_discount_percent(row["HireRateWeekly"], custom_price)
                    st.markdown(f"**{discount_percent:.0f}%**")
                    if discount_percent > row["Max Discount"]:
                        st.warning(f"⚠️ Exceeds Max Discount ({row['Max Discount']}%)")

                df.at[idx, "CustomPrice"] = custom_price
                df.at[idx, "DiscountPercent"] = discount_percent

    # -------------------------------
    # Save Progress Button (with timestamp and download)
    # -------------------------------
    if st.button("💾Save Progress"):
        import datetime
        safe_customer_name = customer_name.strip().replace(" ", "_").replace("/", "_")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{safe_customer_name}_progress_{timestamp}.json"

        custom_prices = {}
        for idx, row in df.iterrows():
            price_key = f"price_{idx}"
            item_key = str(row["ItemCategory"])
            custom_prices[item_key] = st.session_state.get(price_key, "")

        save_data = {
            "customer_name": customer_name,
            "global_discount": global_discount,
            "group_discounts": {
                key: st.session_state[key]
                for key in st.session_state
                if key.endswith("_discount")
            },
            "custom_prices": custom_prices,
            "transport_charges": {
                key: st.session_state[key]
                for key in st.session_state
                if key.startswith("transport_")
            }
        }
        json_data = json.dumps(save_data, indent=2)

        st.download_button(
            label="Download Progress as JSON",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )


    # -------------------------------
    # Final Price List Display
    # -------------------------------
    st.markdown("### Final Price List")
    st.dataframe(df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly",
        "GroupName", "Sub Section", "CustomPrice", "DiscountPercent"
    ]], use_container_width=True)


    # -------------------------------
    # Additional Table: Manually Entered Custom Prices
    # -------------------------------
    st.markdown("### Manually Entered Custom Prices")

    manual_entries = []

    for idx, row in df.iterrows():
        price_key = f"price_{idx}"
        user_input = st.session_state.get(price_key, "").strip()

        # Only include if the user typed something in the box
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
                continue  # Skip invalid entries

    if manual_entries:
        manual_df = pd.DataFrame(manual_entries)
        st.dataframe(manual_df, use_container_width=True)
    else:
        st.info("No manual custom prices have been entered.")






    # -------------------------------
    # Transport Charges Section (with default values)
    # -------------------------------
    st.markdown("### Transport Charges")

    transport_types = [
        "Standard - small tools", "Towables", "Non-mechanical", "Fencing",
        "Tower", "Powered Access", "Low-level Access", "Long Distance"
    ]

    # Default values in the same order
    default_charges = ["5", "7.5", "10", "15", "5", "Negotiable", "5", "15"]

    transport_inputs = []

    for i, (transport_type, default_value) in enumerate(zip(transport_types, default_charges)):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{transport_type}**")
        with col2:
            charge = st.text_input(
                f"Charge for {transport_type}",
                value=default_value,
                key=f"transport_{i}",
                label_visibility="collapsed"
            )
            transport_inputs.append({
                "Delivery or Collection type": transport_type,
                "Charge (£)": charge
            })

    # Create a DataFrame from the inputs
    transport_df = pd.DataFrame(transport_inputs)

    # Display the table
    st.markdown("### Transport Charges Summary")
    st.dataframe(transport_df, use_container_width=True)





    # -------------------------------
    # Excel Export
    # -------------------------------
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="Download as Excel",
        data=output_excel.getvalue(),
        file_name="custom_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # -------------------------------
    # PDF Generation
    # -------------------------------

    # Add a checkbox for including the custom price table
    include_custom_table = st.checkbox("Include Speical Rates at top of PDF", value=True)

    # Add a checkbox for page break after special rates
    special_rates_pagebreak = st.checkbox("Seperate Special Rates on their own page", value=False)

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle

    # Add these custom styles after styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='LeftHeading2',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=6,
        textColor='#002D56'  # Set font color
    ))
    styles.add(ParagraphStyle(
        name='LeftHeading3',
        parent=styles['Heading3'],
        alignment=TA_LEFT,
        spaceBefore=2,
        spaceAfter=4,
        textColor='#002D56'  # Set font color
    ))

    # Add this custom style for the group header (full-width bar)
    styles.add(ParagraphStyle(
        name='BarHeading2',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        textColor='white',
        fontSize=14,
        leftIndent=0,      # Remove left indent
        rightIndent=0,     # Remove right indent
        backColor='#002D56',
        borderPadding=8,   # More padding for a thicker bar
        padding=0,         # No extra padding
        leading=18,        # Line height
    ))

    # --- Custom Price Products Table at the Top (optional) ---
    if include_custom_table:
        custom_price_rows = []
        for idx, row in df.iterrows():
            price_key = f"price_{idx}"
            user_input = str(st.session_state.get(price_key, "")).strip()
            if user_input:
                try:
                    entered_price = float(user_input)
                    custom_price_rows.append([
                        row["ItemCategory"],
                        Paragraph(row["EquipmentName"], styles['BodyText']),
                        f"£{entered_price:.2f}"
                    ])
                except ValueError:
                    continue

        if custom_price_rows:
            customer_title = customer_name if customer_name else "Customer"
            elements.append(Paragraph(f"Net Rates for {customer_title}", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Special Rates", styles['Heading2']))
            elements.append(Spacer(1, 6))
            table_data = [["Category", "Equipment", "Special (£)"]]
            table_data.extend(custom_price_rows)
            row_styles = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ]
            table = Table(table_data, colWidths=[60, 380, 60])
            table.setStyle(TableStyle(row_styles))
            elements.append(table)
            elements.append(Spacer(1, 12))
            # Insert a page break if the user wants the special rates table on its own page
            if special_rates_pagebreak:
                from reportlab.platypus import PageBreak
                elements.append(PageBreak())
    else:
        # If not including custom table, still show the main title
        customer_title = customer_name if customer_name else "Customer"
        elements.append(Paragraph(f"Net Rates for {customer_title}", styles['Title']))
        elements.append(Spacer(1, 12))

    # --- Main Price List Tables ---
    table_col_widths = [60, 380, 60]
    bar_width = sum(table_col_widths)

    for group, group_df in df.groupby("GroupName"):
        group_elements = []

        # Group header bar (dark blue)
        bar_table = Table(
            [[Paragraph(f"{group}", styles['BarHeading2'])]],
            colWidths=[bar_width]
        )
        bar_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), '#002D56'),
            ('TEXTCOLOR', (0, 0), (-1, -1), 'white'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        group_spacer = Spacer(1, 2)
        group_subsection_blocks = []

        # Subsection header bar (light blue) - ensure same width as group bar
        for subsection, sub_df in group_df.groupby("Sub Section"):
            if pd.isnull(subsection) or str(subsection).strip() == "" or subsection == "nan":
                subsection_title = "Untitled"
            else:
                subsection_title = str(subsection)
            subsection_bar = Table(
                [[Paragraph(f"<i>{subsection_title}</i>", styles['LeftHeading3'])]],
                colWidths=[bar_width]  # <-- Ensure this matches bar_table
            )
            subsection_bar.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), '#e6eef7'),
                ('TEXTCOLOR', (0, 0), (-1, -1), '#002D56'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            subsection_spacer = Spacer(1, 2)

            # Table data (no header, no grid)
            table_data = []
            for _, row in sub_df.iterrows():
                table_data.append([
                    row["ItemCategory"],
                    Paragraph(row["EquipmentName"], styles['BodyText']),
                    f"£{row['CustomPrice']:.2f}"
                ])
            table = Table(table_data, colWidths=table_col_widths, repeatRows=0)
            table.setStyle(TableStyle([
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            group_subsection_blocks.append(
                [subsection_bar, subsection_spacer, table, Spacer(1, 12)]
            )

        # Now, for the first subsection, wrap group bar + first subsection in KeepTogether
        if group_subsection_blocks:
            group_elements.append(
                KeepTogether([
                    bar_table,
                    group_spacer,
                    *group_subsection_blocks[0]
                ])
            )
            # Add the rest of the subsections as normal (each in their own KeepTogether)
            for block in group_subsection_blocks[1:]:
                group_elements.append(KeepTogether(block))
        else:
            group_elements.append(
                KeepTogether([
                    bar_table,
                    group_spacer
                ])
            )

        elements.extend(group_elements)

    # NOTE: Transport Charges table is now drawn directly on page 3 of the header PDF.
    # We skip adding it here to avoid duplication.

    doc.build(elements, onFirstPage=add_footer_logo, onLaterPages=add_footer_logo)
    pdf_buffer.seek(0)


    # -------------------------------
    # Merge Header PDF with Generated PDF doc
    # -------------------------------
    header_data = read_pdf_header(header_pdf_file)
    header_pdf = fitz.open(stream=header_data, filetype="pdf")

    # Ensure there are at least 3 pages
    while len(header_pdf) < 3:
        header_pdf.new_page()

    # Add customer name and logo to the first page
    page1 = header_pdf[0]
    if customer_name:
        font_size = 22
        font_color = (0 / 255, 45 / 255, 86 / 255)
        font_name = "helv"
        page_width = page1.rect.width
        page_height = page1.rect.height
        text_y = page_height / 3
        font = fitz.Font(fontname=font_name)
        text_width = font.text_length(customer_name, fontsize=font_size)
        text_x = (page_width - text_width) / 2
        page1.insert_text((text_x, text_y), customer_name, fontsize=font_size, fontname=font_name, fill=font_color)

        # Add bespoke email address below customer name if provided
        if bespoke_email.strip():
            email_font_size = 13
            email_font_color = (0 / 255, 45 / 255, 86 / 255)  # #002D56
            email_text_y = text_y + font_size + 6  # Slightly below customer name
            email_text_width = font.text_length(bespoke_email, fontsize=email_font_size)
            email_text_x = (page_width - email_text_width) / 2
            page1.insert_text(
                (email_text_x, email_text_y),
                bespoke_email,
                fontsize=email_font_size,
                fontname=font_name,
                fill=email_font_color
            )

    if logo_file:
        logo_image = Image.open(logo_file)
        logo_bytes = io.BytesIO()
        logo_image.save(logo_bytes, format="PNG")
        logo_bytes.seek(0)
        logo_width = 100
        logo_height = logo_image.height * (logo_width / logo_image.width)
        logo_x = (page_width - logo_width) / 2
        # Place logo below the email if present, otherwise below the name
        if bespoke_email.strip():
            logo_y = email_text_y + email_font_size + 20
        else:
            logo_y = text_y + font_size + 20
        rect_logo = fitz.Rect(logo_x, logo_y, logo_x + logo_width, logo_y + logo_height)
        page1.insert_image(rect_logo, stream=logo_bytes.read())


    # Draw Transport Charges table as a grid on page 3
    page3 = header_pdf[2]
    page_width = page3.rect.width
    page_height = page3.rect.height

    row_height = 22
    col_widths = [300, 100]
    font_size = 10
    text_padding_x = 6
    text_offset_y = 2  # Adjust text vertical alignment

    # Calculate total table height
    num_rows = len(transport_df) + 1  # +1 for header
    table_height = num_rows * row_height

    # Position table so its bottom is ~1 cm (28.35 pts) from bottom of page
    bottom_margin_cm = 28.35
    margin_y = bottom_margin_cm + table_height

    # Center table horizontally
    table_width = sum(col_widths)
    margin_x = (page_width - table_width) / 2

    # Header color: #7DA6DB → RGB
    header_fill_color = (125 / 255, 166 / 255, 219 / 255)

    # Table header
    headers = ["Delivery or Collection type", "Charge (£)"]
    data_rows = transport_df.values.tolist()

    # Draw header row
    for col_index, header in enumerate(headers):
        x0 = margin_x + sum(col_widths[:col_index])
        x1 = x0 + col_widths[col_index]
        y_text = page_height - margin_y + text_offset_y
        y_rect = page_height - margin_y - 14 #height
        page3.draw_rect(fitz.Rect(x0, y_rect, x1, y_rect + row_height), color=(0.7, 0.7, 0.7), fill=header_fill_color)
        page3.insert_text((x0 + text_padding_x, y_text), header, fontsize=font_size, fontname="helv")

    # Draw data rows
    for row_index, row in enumerate(data_rows):
        for col_index, cell in enumerate(row):
            x0 = margin_x + sum(col_widths[:col_index])
            x1 = x0 + col_widths[col_index]
            y_text = page_height - margin_y + row_height * (row_index + 1) + text_offset_y
            y_rect = page_height - margin_y + row_height * (row_index + 1) - 14 #height
            page3.draw_rect(fitz.Rect(x0, y_rect, x1, y_rect + row_height), color=(0.7, 0.7, 0.7))
            page3.insert_text((x0 + text_padding_x, y_text), str(cell), fontsize=font_size, fontname="helv")




    # Merge with generated PDF
    modified_header = io.BytesIO()
    header_pdf.save(modified_header)
    header_pdf.close()

    merged_pdf = fitz.open(stream=modified_header.getvalue(), filetype="pdf")
    generated_pdf = fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf")
    merged_pdf.insert_pdf(generated_pdf)
    merged_output = io.BytesIO()
    merged_pdf.save(merged_output)
    merged_pdf.close()

    # PDF Download Button
    st.download_button(
        label="Download as PDF",
        data=merged_output.getvalue(),
        file_name="custom_price_list.pdf",
        mime="application/pdf"
    )

# -------------------------------
# Load Progress from Uploaded JSON Only
# -------------------------------
#if st.session_state.get("scroll_to_load"):
 #   st.markdown("## <span style='color:#1976d2'>📂 <b>Load Progress Section</b></span>", unsafe_allow_html=True)
 #   st.session_state["scroll_to_load"] = False

st.markdown("### Load Progress from a Progress JSON File")

uploaded_progress = st.file_uploader(
    "Upload a Progress JSON", type=["json"], key="progress_json_upload"
)

if uploaded_progress and st.button("Load Progress"):
    try:
        loaded_data = json.load(uploaded_progress)
        source = "uploaded file"

        # Clear relevant session state keys
        for key in list(st.session_state.keys()):
            if key.endswith("_discount") or key.startswith("price_") or key.startswith("transport_"):
                del st.session_state[key]
        st.session_state["customer_name"] = loaded_data.get("customer_name", "")
        st.session_state["global_discount"] = loaded_data.get("global_discount", 0.0)
        for key, value in loaded_data.get("group_discounts", {}).items():
            st.session_state[key] = value
        # Restore custom prices using ItemCategory as key
        custom_prices = loaded_data.get("custom_prices", {})
        found_count = 0
        for idx, row in df.iterrows():
            item_key = str(row["ItemCategory"])
            price_key = f"price_{idx}"
            if item_key in custom_prices:
                st.session_state[price_key] = custom_prices[item_key]
                found_count += 1
        for key, value in loaded_data.get("transport_charges", {}).items():
            st.session_state[key] = value
        st.success(f"Progress loaded from {source}! {found_count} custom prices restored.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load progress: {e}")






















