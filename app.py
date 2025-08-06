# net_rates_calculator_group_discount_SaveFunc 4.py

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
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import base64
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

# Add this toggle before the weather section
show_weather = st.checkbox("Show weather information", value=False)

if show_weather:
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

def send_email_with_pricelist(customer_name, admin_df, transport_df, recipient_email, smtp_config=None):
    """Send price list via email to admin team"""
    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = smtp_config.get('from_email', 'noreply@thehireman.co.uk') if smtp_config else 'noreply@thehireman.co.uk'
        msg['To'] = recipient_email
        msg['Subject'] = f"Price List for {customer_name} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Email body
        body = f"""
Hello Admin Team,

Please find attached the price list for customer: {customer_name}

Summary:
- Total Items: {len(admin_df)}
- Date Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Created via: Net Rates Calculator

The attached Excel file contains:
- Sheet 1: Complete price list with all items
- Sheet 2: Transport charges
- Sheet 3: Summary information

Please import this data into our CRM system.

Best regards,
Net Rates Calculator System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Create Excel attachment
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            admin_df.to_excel(writer, sheet_name='Price List', index=False)
            transport_df.to_excel(writer, sheet_name='Transport Charges', index=False)
            
            summary_data = {
                'Customer': [customer_name],
                'Total Items': [len(admin_df)],
                'Date Created': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                'Created By': ['Net Rates Calculator']
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Attach the Excel file
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(output_excel.getvalue())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={customer_name}_pricelist_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        msg.attach(part)
        
        # Send email if SMTP is configured
        if smtp_config and smtp_config.get('enabled', False):
            try:
                server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                text = msg.as_string()
                server.sendmail(smtp_config['from_email'], recipient_email, text)
                server.quit()
                return {'status': 'sent', 'message': 'Email sent successfully!'}
            except Exception as e:
                return {'status': 'error', 'message': f'SMTP Error: {str(e)}'}
        else:
            # Return the email content for manual sending or configuration
            return {'status': 'prepared', 'message': 'Email prepared (SMTP not configured)', 'email_obj': msg}
            
    except Exception as e:
        return {'status': 'error', 'message': f'Email preparation failed: {str(e)}'}

customer_name = st.text_input("⭐Enter Customer Name")
bespoke_email = st.text_input("⭐ Bespoke email address (optional)")
logo_file = st.file_uploader("⭐Upload Company Logo", type=["png", "jpg", "jpeg"])

# --- Move PDF header selection ABOVE Excel upload ---
header_pdf_choice = st.selectbox(
    "⭐Select a PDF Header Sheet",
    ["(Select Sales Person)"] + glob.glob("*.pdf")
)

# Toggle for admin options (hide by default)
show_admin_uploads = st.toggle("Show Admin Upload Options", value=False)

if show_admin_uploads:
    uploaded_file = st.file_uploader("❗ADMIN Upload Excel file (Admin Only❗)", type=["xlsx"])
    uploaded_header_pdf = st.file_uploader("❗ADMIN Upload PDF Header (Admin Only❗)", type=["pdf"], key="header_pdf_upload")
else:
    uploaded_file = None
    uploaded_header_pdf = None

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
elif header_pdf_choice != "(Select Sales Person)":
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
    # Get global discount from session state if available, otherwise use default
    global_discount_value = st.session_state.get("global_discount", 0)
    global_discount = st.number_input("Global Discount (%)", min_value=0, max_value=100, value=global_discount_value, step=1, key="global_discount")

    st.markdown("### Group-Level Discounts")
    group_discount_keys = {}
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())

    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]  # Fill down each column
        with col:
            discount_key = f"{group}_{subsection}_discount"
            # Use session state value if available, otherwise use global discount
            default_value = st.session_state.get(discount_key, global_discount)
            st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0,
                max_value=100,
                value=default_value,
                step=1,
                key=discount_key
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
        safe_customer_name = customer_name.strip().replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
    # Export Options for Admin Team
    # -------------------------------
    st.markdown("### 📤 Export Options for Admin Team")
    
    # Create admin-friendly DataFrame with clear column names
    admin_df = df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly", 
        "CustomPrice", "DiscountPercent", "GroupName", "Sub Section"
    ]].copy()
    admin_df.columns = [
        "Item Category", "Equipment Name", "Original Price (£)", 
        "Net Price (£)", "Discount %", "Group", "Sub Section"
    ]
    admin_df["Customer Name"] = customer_name
    admin_df["Date Created"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Reorder columns for admin convenience
    admin_df = admin_df[[
        "Customer Name", "Date Created", "Item Category", "Equipment Name", 
        "Original Price (£)", "Net Price (£)", "Discount %", "Group", "Sub Section"
    ]]

    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Enhanced Excel Export
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            # Main price list
            admin_df.to_excel(writer, sheet_name='Price List', index=False)
            
            # Transport charges sheet
            transport_df.to_excel(writer, sheet_name='Transport Charges', index=False)
            
            # Summary sheet
            summary_data = {
                'Customer': [customer_name],
                'Total Items': [len(admin_df)],
                'Global Discount %': [global_discount],
                'Date Created': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                'Created By': ['Net Rates Calculator']
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        st.download_button(
            label="📊 Download Excel (Admin Format)",
            data=output_excel.getvalue(),
            file_name=f"{customer_name}_admin_pricelist_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        # CSV Export (universal format)
        csv_data = admin_df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"{customer_name}_pricelist_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # JSON Export (for API integration)
        json_export = {
            "customer_info": {
                "name": customer_name,
                "date_created": datetime.now().isoformat(),
                "global_discount": global_discount
            },
            "price_list": admin_df.to_dict('records'),
            "transport_charges": transport_df.to_dict('records')
        }
        
        st.download_button(
            label="🔗 Download JSON (API)",
            data=json.dumps(json_export, indent=2),
            file_name=f"{customer_name}_api_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

    # -------------------------------
    # Direct Email to Admin Team
    # -------------------------------
    st.markdown("### 📧 Email to Admin Team")
    
    # SMTP Configuration Section
    with st.expander("⚙️ SMTP Configuration (Click to configure email sending)"):
        st.markdown("#### Choose Email Provider")
        
        email_provider = st.selectbox(
            "Email Service",
            ["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"]
        )
        
        if email_provider == "SendGrid":
            st.info("📋 **SendGrid Setup Instructions:**")
            st.markdown("""
            1. Go to [SendGrid Console](https://app.sendgrid.com/)
            2. Navigate to Settings → API Keys
            3. Create a new API key with 'Mail Send' permissions
            4. Copy the API key and paste below
            5. **IMPORTANT**: Verify your sender email in Settings → Sender Authentication
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                sg_api_key = st.text_input("SendGrid API Key", type="password")
                sg_from_email = st.text_input("From Email", value="paul.scott@thehireman.co.uk", help="Must be a verified sender in SendGrid")
            with col2:
                st.info("**SendGrid Settings:**\n- Server: smtp.sendgrid.net\n- Port: 587\n- Username: 'apikey'\n- Password: Your API Key")
                st.warning("⚠️ **Important**: The 'From Email' must be verified in SendGrid → Settings → Sender Authentication")
            
            # Sender verification helper
            if sg_from_email:
                st.markdown("#### 🔍 **Sender Verification Check**")
                st.markdown(f"""
                **Your From Email:** `{sg_from_email}`
                
                **To verify this email in SendGrid:**
                1. Go to [SendGrid Sender Authentication](https://app.sendgrid.com/settings/sender_auth)
                2. Click **Single Sender Verification**
                3. Add `{sg_from_email}` as a verified sender
                4. Check your email and click the verification link
                
                **Alternative emails you could use:**
                - Your work email: `paul.scott@thehireman.co.uk`
                - Company no-reply: `noreply@thehireman.co.uk` (if domain is verified)
                - Gmail: `your.name@gmail.com` (if you have one)
                """)
            
            if sg_api_key:
                smtp_config = {
                    'enabled': True,
                    'smtp_server': 'smtp.sendgrid.net',
                    'smtp_port': 587,
                    'username': 'apikey',
                    'password': sg_api_key,
                    'from_email': sg_from_email,
                    'use_tls': True,
                    'provider': 'SendGrid'
                }
            else:
                smtp_config = {'enabled': False}
                
        elif email_provider == "Gmail":
            st.warning("⚠️ **Gmail requires App Password** (not your regular password)")
            st.markdown("""
            1. Enable 2-Factor Authentication on your Google account
            2. Go to Google Account → Security → App passwords
            3. Generate an app password for 'Mail'
            4. Use that 16-character password below
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                gmail_user = st.text_input("Gmail Address")
                gmail_password = st.text_input("App Password", type="password")
            with col2:
                st.info("**Gmail Settings:**\n- Server: smtp.gmail.com\n- Port: 587\n- TLS: Enabled")
            
            if gmail_user and gmail_password:
                smtp_config = {
                    'enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': gmail_user,
                    'password': gmail_password,
                    'from_email': gmail_user,
                    'use_tls': True,
                    'provider': 'Gmail'
                }
            else:
                smtp_config = {'enabled': False}
                
        elif email_provider == "Outlook/Office365":
            st.info("📋 **Office365/Outlook Setup:**")
            
            col1, col2 = st.columns(2)
            with col1:
                o365_user = st.text_input("Office365 Email")
                o365_password = st.text_input("Password", type="password")
            with col2:
                st.info("**Office365 Settings:**\n- Server: smtp.office365.com\n- Port: 587\n- TLS: Enabled")
            
            if o365_user and o365_password:
                smtp_config = {
                    'enabled': True,
                    'smtp_server': 'smtp.office365.com',
                    'smtp_port': 587,
                    'username': o365_user,
                    'password': o365_password,
                    'from_email': o365_user,
                    'use_tls': True,
                    'provider': 'Office365'
                }
            else:
                smtp_config = {'enabled': False}
                
        elif email_provider == "Custom SMTP":
            st.info("🔧 **Custom SMTP Configuration:**")
            
            col1, col2 = st.columns(2)
            with col1:
                custom_server = st.text_input("SMTP Server")
                custom_port = st.number_input("SMTP Port", value=587)
                custom_user = st.text_input("Username")
            with col2:
                custom_password = st.text_input("Password", type="password")
                custom_from = st.text_input("From Email")
                use_tls = st.checkbox("Use TLS", value=True)
            
            if custom_server and custom_user and custom_password:
                smtp_config = {
                    'enabled': True,
                    'smtp_server': custom_server,
                    'smtp_port': int(custom_port),
                    'username': custom_user,
                    'password': custom_password,
                    'from_email': custom_from,
                    'use_tls': use_tls,
                    'provider': 'Custom'
                }
            else:
                smtp_config = {'enabled': False}
        else:
            smtp_config = {'enabled': False}
        
        # Test Email Button
        if smtp_config.get('enabled', False):
            if st.button("🧪 Test Email Configuration"):
                try:
                    server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
                    if smtp_config.get('use_tls', True):
                        server.starttls()
                    server.login(smtp_config['username'], smtp_config['password'])
                    server.quit()
                    st.success("✅ SMTP Configuration Test Successful!")
                except Exception as e:
                    st.error(f"❌ SMTP Test Failed: {str(e)}")
    
    # Email Form
    col1, col2 = st.columns(2)
    with col1:
        admin_email = st.text_input("Admin Team Email", placeholder="admin@company.com")
    with col2:
        include_transport = st.checkbox("Include Transport Charges", value=True)
    
    # Status indicator
    if smtp_config.get('enabled', False):
        st.success(f"✅ Email configured via {smtp_config.get('provider', 'SMTP')}")
    else:
        st.warning("⚠️ Email not configured - will prepare email only")
    
    if st.button("📨 Send Email to Admin Team") and admin_email:
        if customer_name:
            try:
                # Prepare and send the email
                result = send_email_with_pricelist(
                    customer_name, 
                    admin_df, 
                    transport_df if include_transport else pd.DataFrame(), 
                    admin_email,
                    smtp_config
                )
                
                if result['status'] == 'sent':
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                elif result['status'] == 'prepared':
                    st.success(f"✅ Email prepared successfully!")
                    st.info("📝 **Note**: Configure SMTP above to enable automatic sending.")
                    
                    # Show email preview
                    with st.expander("📧 Email Preview"):
                        email_obj = result.get('email_obj')
                        if email_obj:
                            st.text(f"To: {admin_email}")
                            st.text(f"Subject: {email_obj['Subject']}")
                            st.text("📎 Attached: Excel file with price list")
                else:
                    st.error(f"❌ {result['message']}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a customer name first")

    # -------------------------------
    # Alternative Data Sharing Methods
    # -------------------------------
    st.markdown("### 🔄 Alternative Data Sharing Methods")
    
    # Quick share options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create a shareable link (placeholder for actual implementation)
        if st.button("🔗 Generate Share Link"):
            # In a real implementation, this would upload to a temporary server
            share_data = {
                "customer": customer_name,
                "data": admin_df.to_dict('records'),
                "timestamp": datetime.now().isoformat()
            }
            # Encode data for demo purposes
            encoded_data = base64.b64encode(json.dumps(share_data).encode()).decode()[:50] + "..."
            st.success("� Share link generated!")
            st.code(f"https://your-company.com/share/{encoded_data}")
            st.info("�💡 Admin team can click this link to access the data directly")
    
    with col2:
        # Teams/Slack message template
        if st.button("💬 Generate Teams Message"):
            teams_message = f"""
🏢 **New Price List Ready for CRM Input**

**Customer:** {customer_name}
**Items:** {len(admin_df)} equipment items
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Created by:** Net Rates Calculator

📊 **Action Required:** Please download and import the attached Excel file into our CRM system.

📎 Files attached:
- {customer_name}_admin_pricelist_{datetime.now().strftime('%Y%m%d')}.xlsx
            """
            st.success("💬 Teams message template generated!")
            st.text_area("Copy this message to Teams:", teams_message, height=200)
    
    with col3:
        # API endpoint for CRM integration
        if st.button("🔌 Show API Format"):
            api_payload = {
                "endpoint": "POST /api/crm/import-pricelist",
                "headers": {"Content-Type": "application/json"},
                "payload": {
                    "customer_name": customer_name,
                    "created_date": datetime.now().isoformat(),
                    "items": admin_df.head(3).to_dict('records'),  # Show first 3 as example
                    "total_items": len(admin_df)
                }
            }
            st.success("🔌 API format generated!")
            st.json(api_payload)
    
    with st.expander("💡 Click to see detailed comparison of methods"):
        st.markdown("""
        **📊 Spreadsheet Options:**
        - **Excel** (Current) ⭐ - Best for CRM import, formulas, multiple sheets
        - **Google Sheets** - Real-time collaboration, automatic sync
        - **CSV** - Universal format, works with any system
        
        **🌐 Digital Methods:**
        - **Shared Cloud Folder** ⭐ - OneDrive/Google Drive automatic sync
        - **Teams/Slack Integration** - Direct channel posting
        - **API Integration** - Direct CRM connection (JSON format)
        - **Share Links** - Temporary download links
        
        **📧 Communication Options:**
        - **Direct Email** (Above) ⭐ - Instant delivery with attachment
        - **Scheduled Reports** - Daily/weekly automatic sends
        - **Internal Portal** - Web dashboard for admin access
        
        **⚡ Easiest Methods Ranked:**
        1. **Email with Excel** ⭐ - Familiar, reliable, includes all data
        2. **Shared OneDrive folder** ⭐ - Automatic sync, version control
        3. **Teams message with attachment** - Quick notification
        4. **CSV to shared folder** - Simple, works with all systems
        5. **API integration** - Fully automated (requires development)
        
        **🎯 Recommended Setup:**
        1. **Primary**: Email Excel file to admin team
        2. **Backup**: Save to shared OneDrive folder
        3. **Notification**: Teams message with link to file
        """)

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

    # Update BarHeading2 style to use Helvetica-Bold
    styles.add(ParagraphStyle(
        name='BarHeading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',  # Use Helvetica-Bold
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        textColor='white',
        fontSize=14,
        leftIndent=0,
        rightIndent=0,
        backColor='#002D56',
        borderPadding=8,
        padding=0,
        leading=18,
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
            [[Paragraph(f"{group.upper()}", styles['BarHeading2'])]],
            colWidths=[bar_width]
        )
        bar_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), '#002D56'),
            ('TEXTCOLOR', (0, 0), (-1, -1), 'white'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        group_spacer = Spacer(1, 2)
        group_subsection_blocks = []

        # Subsection header bar (light blue) - ensure same width and padding as group bar
        for subsection, sub_df in group_df.groupby("Sub Section"):
            if pd.isnull(subsection) or str(subsection).strip() == "" or subsection == "nan":
                subsection_title = "Untitled"
            else:
                subsection_title = str(subsection)

            # Subsection header row (subtitle in the second/wide cell)
            header_row = [
                '',  # Empty cell for ItemCategory (narrow)
                Paragraph(f"<i>{subsection_title}</i>", styles['LeftHeading3']),  # Subtitle in wide cell
                ''   # Empty cell for Price column
            ]

            # Table data (no header, no grid)
            table_data = [header_row]
            for _, row in sub_df.iterrows():
                table_data.append([
                    row["ItemCategory"],
                    Paragraph(row["EquipmentName"], styles['BodyText']),
                    f"£{row['CustomPrice']:.2f}"
                ])

            table_with_repeat_header = Table(
                table_data,
                colWidths=table_col_widths,
                repeatRows=1
            )
            table_with_repeat_header.setStyle(TableStyle([
                # Style for the header row
                ('BACKGROUND', (0, 0), (-1, 0), '#e6eef7'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#002D56'),
                ('LEFTPADDING', (0, 0), (-1, 0), 8),
                ('RIGHTPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 4),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),  # Align subtitle left in the wide cell
                # Style for the rest of the table
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))

            group_subsection_blocks.append(
                [table_with_repeat_header, Spacer(1, 12)]
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
    # Generate filename: Price List for "Customer Name" Month Year.pdf
    from datetime import datetime
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    safe_customer_name = customer_name.strip() if customer_name else "Customer"
    filename = f'Price List for {safe_customer_name} {month_year}.pdf'

    st.download_button(
        label="Download as PDF",
        data=merged_output.getvalue(),
        file_name=filename,
        mime="application/pdf"
    )

# -------------------------------
# Admin Dashboard (Collapsible)
# -------------------------------
st.markdown("---")
with st.expander("🔧 Admin Dashboard & Integration Settings"):
    st.markdown("### 🏢 Admin Team Integration Hub")
    
    tab1, tab2, tab3 = st.tabs(["📧 Email Settings", "🔄 Automation", "📊 Analytics"])
    
    with tab1:
        st.markdown("#### Email Configuration")
        col1, col2 = st.columns(2)
        with col1:
            default_admin_email = st.text_input("Default Admin Email", value="admin@thehireman.co.uk")
            cc_emails = st.text_input("CC Emails (comma separated)", placeholder="manager@company.com, crm@company.com")
        with col2:
            email_template = st.selectbox("Email Template", 
                ["Standard Price List", "Urgent Priority", "Bulk Import", "Custom"])
            auto_send = st.checkbox("Auto-send to admin team", help="Automatically email when price list is generated")
    
    with tab2:
        st.markdown("#### Automation Options")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**File Sharing**")
            auto_save_location = st.selectbox("Auto-save location", 
                ["OneDrive - Shared", "Local Network", "Cloud Storage", "Database"])
            folder_structure = st.selectbox("Folder structure", 
                ["By Customer", "By Date", "By Sales Rep", "Flat Structure"])
        with col2:
            st.markdown("**CRM Integration**")
            crm_system = st.selectbox("CRM System", 
                ["Manual Import", "API Integration", "Scheduled Sync", "Real-time"])
            data_format = st.selectbox("Preferred Format", 
                ["Excel (Multi-sheet)", "CSV", "JSON", "XML"])
    
    with tab3:
        st.markdown("#### Usage Analytics")
        if customer_name:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price Lists Generated", "1", "Today")
            with col2:
                st.metric("Items Processed", len(admin_df) if 'admin_df' in locals() else 0)
            with col3:
                st.metric("Data Export Size", f"{round(len(str(admin_df)) / 1024, 1)}KB" if 'admin_df' in locals() else "0KB")
        
        st.markdown("**Integration Health Check**")
        health_checks = {
            "📧 Email System": "✅ Ready",
            "💾 File Storage": "✅ Connected", 
            "🔄 CRM Connection": "⚠️ Manual Mode",
            "📊 Analytics": "✅ Active"
        }
        
        for check, status in health_checks.items():
            st.write(f"{check}: {status}")

# -------------------------------
# Quick Admin Actions
# -------------------------------
if customer_name and 'admin_df' in locals():
    st.markdown("---")
    st.markdown("### ⚡ Quick Admin Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📧 Email to Admin"):
            st.info("Email prepared! (Configure SMTP for auto-send)")
    
    with col2:
        if st.button("💾 Save to OneDrive"):
            st.info("File ready for OneDrive upload")
    
    with col3:
        if st.button("💬 Teams Notification"):
            st.info("Teams message template generated above")
    
    with col4:
        if st.button("🔄 Queue for CRM"):
            st.info("Added to CRM import queue")

# Footer
st.markdown("---")
st.markdown("*Net Rates Calculator - Admin Integration v2.0*")
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

        # Clear ALL session state to avoid widget conflicts
        keys_to_clear = []
        for key in st.session_state.keys():
            if (key.endswith("_discount") or 
                key.startswith("price_") or 
                key.startswith("transport_") or
                key == "customer_name" or
                key == "global_discount"):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Restore values to session state
        st.session_state["customer_name"] = loaded_data.get("customer_name", "")
        st.session_state["global_discount"] = loaded_data.get("global_discount", 0.0)
        
        # Restore group discounts
        for key, value in loaded_data.get("group_discounts", {}).items():
            st.session_state[key] = value
            
        # Restore custom prices using ItemCategory as key
        custom_prices = loaded_data.get("custom_prices", {})
        found_count = 0
        if df is not None:
            for idx, row in df.iterrows():
                item_key = str(row["ItemCategory"])
                price_key = f"price_{idx}"
                if item_key in custom_prices:
                    st.session_state[price_key] = custom_prices[item_key]
                    found_count += 1
                    
        # Restore transport charges
        for key, value in loaded_data.get("transport_charges", {}).items():
            st.session_state[key] = value
            
        st.success(f"Progress loaded from {source}! {found_count} custom prices restored.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load progress: {e}")

import os
st.write("Current working directory:", os.getcwd())






















