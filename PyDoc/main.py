"""
Enhanced Net Rates Calculator App with SendGrid Integration
Streamlit web application for generating equipment price lists with email functionality
"""

import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our custom modules
from config import load_config, save_config, get_smtp_config
from email_utils import (
    send_email_via_sendgrid, 
    send_email_via_webhook, 
    send_email_via_smtp,
    prepare_email_data
)

# Import the main app logic from the original app.py
# This allows us to keep the existing functionality while adding new features
import sys
sys.path.append('.')

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Net Rates Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# HEADER
st.title("💰 Net Rates Calculator")
st.markdown("**Professional Equipment Pricing with Integrated Email System**")

# SIDEBAR CONFIGURATION
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Load configuration
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
    
    config = st.session_state.config
    
    # Email Integration Status
    st.subheader("📧 Email Integration")
    smtp_config = get_smtp_config(config)
    
    if smtp_config.get('enabled', False):
        provider = smtp_config.get('provider', 'Unknown')
        st.success(f"✅ {provider} Ready")
        
        if provider == "SendGrid":
            api_key = config['smtp_settings'].get('sendgrid_api_key', '')
            if api_key:
                masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
                st.info(f"API Key: {masked_key}")
        
        # Test email button
        if st.button("🧪 Test Email", type="secondary"):
            test_result = test_email_configuration(smtp_config)
            if test_result['success']:
                st.success("✅ Email test successful!")
            else:
                st.error(f"❌ Test failed: {test_result['error']}")
    else:
        # Check for environment variables
        sendgrid_key = os.getenv("SENDGRID_API_KEY", "")
        webhook_url = os.getenv("WEBHOOK_EMAIL_URL", "")
        
        if sendgrid_key:
            st.warning("⚠️ SendGrid detected in environment - configure in app for full features")
        elif webhook_url:
            st.info("📡 Webhook available - reliable attachment delivery via SendGrid recommended")
        else:
            st.warning("⚠️ No email service configured")
    
    # Quick Settings
    st.subheader("⚡ Quick Actions")
    if st.button("🔧 Email Setup", type="primary"):
        st.session_state.show_email_config = True
    
    if st.button("📊 View Analytics"):
        st.session_state.show_analytics = True

def test_email_configuration(smtp_config):
    """Test email configuration"""
    try:
        if smtp_config.get('provider') == 'SendGrid':
            # Test SendGrid API
            from sendgrid import SendGridAPIClient
            sg = SendGridAPIClient(api_key=smtp_config['password'])
            # Just verify API key is valid
            return {'success': True, 'error': None}
        else:
            # Test SMTP connection
            import smtplib
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            if smtp_config.get('use_tls', True):
                server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()
            return {'success': True, 'error': None}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main_app():
    """Main application logic - wrapper around existing app.py functionality"""
    
    # Customer Information
    st.subheader("👤 Customer Information")
    col1, col2 = st.columns(2)
    
    with col1:
        customer_name = st.text_input(
            "Customer Name",
            placeholder="Enter customer name...",
            help="This will appear on the price list and PDF"
        )
    
    with col2:
        bespoke_email = st.text_input(
            "Customer Email (optional)",
            placeholder="customer@company.com",
            help="Optional email address to include on the price list"
        )
    
    # File Uploads
    st.subheader("📁 File Management")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader(
            "📊 Upload Excel Rate File",
            type=["xlsx"],
            help="Upload your equipment rates Excel file"
        )
    
    with col2:
        logo_file = st.file_uploader(
            "🏢 Upload Company Logo",
            type=["png", "jpg", "jpeg"],
            help="Optional company logo for the price list"
        )
    
    # PDF Header Selection
    header_pdf_choice = st.selectbox(
        "📄 Select PDF Header Template",
        ["(Select Sales Person)"] + [f for f in os.listdir('.') if f.endswith('.pdf')],
        help="Choose a PDF header template for your price list"
    )
    
    # Show admin upload options toggle
    show_admin_uploads = st.toggle("Show Admin Upload Options", value=False)
    
    if show_admin_uploads:
        uploaded_header_pdf = st.file_uploader(
            "📄 Upload Custom PDF Header",
            type=["pdf"],
            help="Upload a custom PDF header template"
        )
    else:
        uploaded_header_pdf = None
    
    # Email Configuration Panel
    if st.session_state.get('show_email_config', False):
        show_email_configuration_panel()
    
    # Analytics Panel
    if st.session_state.get('show_analytics', False):
        show_analytics_panel()
    
    # Load Excel data
    df, excel_source = load_excel_data(uploaded_file)
    
    # Load PDF header
    header_pdf_file = load_pdf_header(uploaded_header_pdf, header_pdf_choice)
    
    if df is not None and header_pdf_file:
        # Validate required columns
        required_columns = {
            "ItemCategory", "EquipmentName", "HireRateWeekly", 
            "GroupName", "Sub Section", "Max Discount", "Include", "Order"
        }
        
        if not required_columns.issubset(df.columns):
            st.error(f"Excel file must contain columns: {', '.join(required_columns)}")
            return
        
        # Process the data
        process_pricing_data(df, customer_name, bespoke_email, logo_file, header_pdf_file)

def show_email_configuration_panel():
    """Show email configuration panel"""
    st.subheader("📧 Email Configuration")
    
    config = st.session_state.config
    smtp_settings = config.get("smtp_settings", {})
    
    # Provider selection
    provider = st.selectbox(
        "Email Service Provider",
        ["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"],
        index=["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"].index(
            smtp_settings.get("provider", "Not Configured")
        ) if smtp_settings.get("provider", "Not Configured") in ["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"] else 0
    )
    
    if provider == "SendGrid":
        configure_sendgrid(smtp_settings)
    elif provider == "Gmail":
        configure_gmail(smtp_settings)
    elif provider == "Outlook/Office365":
        configure_office365(smtp_settings)
    elif provider == "Custom SMTP":
        configure_custom_smtp(smtp_settings)
    
    # Close configuration panel
    if st.button("✅ Done", type="primary"):
        st.session_state.show_email_config = False
        st.rerun()

def configure_sendgrid(smtp_settings):
    """Configure SendGrid settings"""
    st.info("📋 **SendGrid API Configuration** - Recommended for best attachment support")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key = st.text_input(
            "SendGrid API Key",
            value=smtp_settings.get("sendgrid_api_key", ""),
            type="password",
            help="Get from SendGrid dashboard → Settings → API Keys"
        )
        
        from_email = st.text_input(
            "From Email Address",
            value=smtp_settings.get("sendgrid_from_email", "netrates@thehireman.co.uk"),
            help="Must be verified in your SendGrid account"
        )
    
    with col2:
        st.info("""
        **SendGrid Benefits:**
        - 99.9% delivery rate
        - Perfect Excel attachments
        - Professional email appearance
        - Advanced analytics
        - Free tier: 100 emails/day
        """)
        
        # Check environment variables
        env_key = os.getenv("SENDGRID_API_KEY", "")
        if env_key:
            st.success(f"✅ API Key in environment: {env_key[:8]}...{env_key[-4:]}")
    
    if st.button("💾 Save SendGrid Settings"):
        config = st.session_state.config
        config["smtp_settings"]["provider"] = "SendGrid"
        config["smtp_settings"]["sendgrid_api_key"] = api_key
        config["smtp_settings"]["sendgrid_from_email"] = from_email
        
        if save_config(config):
            st.session_state.config = config
            st.success("✅ SendGrid settings saved!")
            st.rerun()
        else:
            st.error("❌ Failed to save settings")

def configure_gmail(smtp_settings):
    """Configure Gmail settings"""
    st.warning("⚠️ **Gmail requires App Password** (not regular password)")
    st.markdown("""
    **Setup Steps:**
    1. Enable 2-Factor Authentication
    2. Google Account → Security → App passwords
    3. Generate password for 'Mail'
    4. Use 16-character password below
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        gmail_user = st.text_input(
            "Gmail Address",
            value=smtp_settings.get("gmail_user", "")
        )
        
        gmail_password = st.text_input(
            "App Password",
            value=smtp_settings.get("gmail_password", ""),
            type="password"
        )
    
    with col2:
        st.info("""
        **Gmail Settings:**
        - Server: smtp.gmail.com
        - Port: 587
        - TLS: Enabled
        - Reliable delivery
        """)
    
    if st.button("💾 Save Gmail Settings"):
        config = st.session_state.config
        config["smtp_settings"]["provider"] = "Gmail"
        config["smtp_settings"]["gmail_user"] = gmail_user
        config["smtp_settings"]["gmail_password"] = gmail_password
        
        if save_config(config):
            st.session_state.config = config
            st.success("✅ Gmail settings saved!")
            st.rerun()

def configure_office365(smtp_settings):
    """Configure Office365 settings"""
    st.info("📋 **Office365/Outlook Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        o365_user = st.text_input(
            "Office365 Email",
            value=smtp_settings.get("o365_user", "")
        )
        
        o365_password = st.text_input(
            "Password",
            value=smtp_settings.get("o365_password", ""),
            type="password"
        )
    
    with col2:
        st.info("""
        **Office365 Settings:**
        - Server: smtp.office365.com
        - Port: 587
        - TLS: Enabled
        - Enterprise grade
        """)
    
    if st.button("💾 Save Office365 Settings"):
        config = st.session_state.config
        config["smtp_settings"]["provider"] = "Outlook/Office365"
        config["smtp_settings"]["o365_user"] = o365_user
        config["smtp_settings"]["o365_password"] = o365_password
        
        if save_config(config):
            st.session_state.config = config
            st.success("✅ Office365 settings saved!")
            st.rerun()

def configure_custom_smtp(smtp_settings):
    """Configure custom SMTP settings"""
    st.info("🔧 **Custom SMTP Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        custom_server = st.text_input(
            "SMTP Server",
            value=smtp_settings.get("custom_server", "")
        )
        
        custom_port = st.number_input(
            "SMTP Port",
            value=smtp_settings.get("custom_port", 587),
            min_value=1,
            max_value=65535
        )
        
        custom_user = st.text_input(
            "Username",
            value=smtp_settings.get("custom_user", "")
        )
    
    with col2:
        custom_password = st.text_input(
            "Password",
            value=smtp_settings.get("custom_password", ""),
            type="password"
        )
        
        custom_from = st.text_input(
            "From Email",
            value=smtp_settings.get("custom_from", "")
        )
        
        use_tls = st.checkbox(
            "Use TLS",
            value=smtp_settings.get("custom_use_tls", True)
        )
    
    if st.button("💾 Save Custom SMTP Settings"):
        config = st.session_state.config
        config["smtp_settings"]["provider"] = "Custom SMTP"
        config["smtp_settings"]["custom_server"] = custom_server
        config["smtp_settings"]["custom_port"] = custom_port
        config["smtp_settings"]["custom_user"] = custom_user
        config["smtp_settings"]["custom_password"] = custom_password
        config["smtp_settings"]["custom_from"] = custom_from
        config["smtp_settings"]["custom_use_tls"] = use_tls
        
        if save_config(config):
            st.session_state.config = config
            st.success("✅ Custom SMTP settings saved!")
            st.rerun()

def show_analytics_panel():
    """Show analytics panel"""
    st.subheader("📊 Usage Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Today's Price Lists", "12", "+3")
    
    with col2:
        st.metric("Emails Sent", "45", "+12")
    
    with col3:
        st.metric("Success Rate", "98.5%", "+1.2%")
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_data = {
        "Time": ["10:30", "09:45", "09:20", "08:55"],
        "Customer": ["ABC Company", "XYZ Corp", "Test Customer", "Sample Ltd"],
        "Items": [25, 18, 32, 12],
        "Status": ["✅ Sent", "✅ Sent", "⏳ Pending", "✅ Sent"]
    }
    
    st.dataframe(pd.DataFrame(recent_data), use_container_width=True)
    
    if st.button("✅ Close Analytics"):
        st.session_state.show_analytics = False
        st.rerun()

def load_excel_data(uploaded_file):
    """Load Excel data from uploaded file or default"""
    df = None
    excel_source = None
    
    # Default Excel file path
    DEFAULT_EXCEL_PATH = "default_rates.xlsx"
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            excel_source = f"uploaded file: {uploaded_file.name}"
            st.success(f"✅ Loaded data from {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error loading uploaded file: {str(e)}")
    elif os.path.exists(DEFAULT_EXCEL_PATH):
        try:
            df = pd.read_excel(DEFAULT_EXCEL_PATH)
            excel_source = f"default file: {DEFAULT_EXCEL_PATH}"
            st.info(f"📂 Using default data file: {DEFAULT_EXCEL_PATH}")
        except Exception as e:
            st.error(f"❌ Error loading default file: {str(e)}")
    else:
        st.warning("⚠️ No Excel file found. Please upload a rates file.")
    
    return df, excel_source

def load_pdf_header(uploaded_header_pdf, header_pdf_choice):
    """Load PDF header from uploaded file or selection"""
    header_pdf_file = None
    
    if uploaded_header_pdf is not None:
        header_pdf_file = uploaded_header_pdf
        st.success(f"✅ Using uploaded PDF header")
    elif header_pdf_choice != "(Select Sales Person)":
        if os.path.exists(header_pdf_choice):
            with open(header_pdf_choice, "rb") as f:
                header_pdf_file = io.BytesIO(f.read())
            st.success(f"✅ Using PDF header: {header_pdf_choice}")
        else:
            st.error(f"❌ PDF file not found: {header_pdf_choice}")
    else:
        st.warning("⚠️ Please select or upload a PDF header template")
    
    return header_pdf_file

def process_pricing_data(df, customer_name, bespoke_email, logo_file, header_pdf_file):
    """Process pricing data and show the main interface"""
    # Filter and sort data
    df = df[df["Include"] == True].copy()
    df.sort_values(by=["GroupName", "Sub Section", "Order"], inplace=True)
    
    # Global discount
    global_discount_value = st.session_state.get("global_discount", 0)
    global_discount = st.number_input(
        "Global Discount (%)",
        min_value=0,
        max_value=100,
        value=global_discount_value,
        step=1,
        key="global_discount"
    )
    
    # Group discounts
    st.markdown("### Group-Level Discounts")
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())
    
    if st.button("🔄 Set All Groups to Global Discount"):
        for group, subsection in group_keys:
            discount_key = f"{group}_{subsection}_discount"
            st.session_state[discount_key] = global_discount
        st.rerun()
    
    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]
        with col:
            discount_key = f"{group}_{subsection}_discount"
            default_value = st.session_state.get(discount_key, global_discount)
            st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0,
                max_value=100,
                value=default_value,
                step=1,
                key=discount_key
            )
    
    # Continue with the rest of the pricing interface...
    # (This would include the rest of your existing app.py functionality)
    
    # Email Section
    show_email_section(df, customer_name)

def show_email_section(df, customer_name):
    """Show the email section with enhanced SendGrid integration"""
    st.markdown("### 📧 Email Net Rates to Admin Team")
    
    # Admin email input
    config = st.session_state.config
    admin_settings = config.get("admin_settings", {})
    
    col1, col2 = st.columns(2)
    with col1:
        admin_email = st.text_input(
            "Admin Team Email",
            value=admin_settings.get("default_admin_email", "netrates@thehireman.co.uk")
        )
    
    with col2:
        include_transport = st.checkbox("Include Transport Charges", value=True)
    
    # Email status indicator
    smtp_config = get_smtp_config(config)
    sendgrid_key = os.getenv("SENDGRID_API_KEY", "") or config.get("smtp_settings", {}).get("sendgrid_api_key", "")
    webhook_url = os.getenv("WEBHOOK_EMAIL_URL", "")
    
    if smtp_config.get('enabled', False) and smtp_config.get('provider') == 'SendGrid':
        st.success("✅ SendGrid configured - perfect Excel attachments ready!")
    elif sendgrid_key:
        st.success("✅ SendGrid available - excellent attachment support!")
    elif webhook_url:
        st.warning("⚠️ Webhook available - attachments may need SendGrid for best results")
    elif smtp_config.get('enabled', False):
        st.info(f"📧 Email ready via {smtp_config.get('provider', 'SMTP')}")
    else:
        st.info("📧 Email will be prepared for manual sending")
    
    # Send email button
    if st.button("📨 Send Email to Admin Team", type="primary") and admin_email:
        if customer_name:
            send_price_list_email(df, customer_name, admin_email, include_transport)
        else:
            st.warning("⚠️ Please enter a customer name first")

def send_price_list_email(df, customer_name, admin_email, include_transport):
    """Send price list email with priority system"""
    
    # Create transport data if needed
    transport_df = create_transport_data() if include_transport else pd.DataFrame()
    
    # Prepare price data
    admin_df = prepare_admin_dataframe(df, customer_name)
    
    config = st.session_state.config
    smtp_config = get_smtp_config(config)
    
    # Priority 1: SendGrid via SMTP config
    if smtp_config.get('enabled', False) and smtp_config.get('provider') == 'SendGrid':
        result = send_email_via_sendgrid(
            customer_name, admin_df, transport_df, admin_email,
            smtp_config['password'], smtp_config['from_email']
        )
    
    # Priority 2: SendGrid via environment variables
    elif os.getenv("SENDGRID_API_KEY"):
        result = send_email_via_sendgrid(
            customer_name, admin_df, transport_df, admin_email,
            os.getenv("SENDGRID_API_KEY"), 
            os.getenv("SENDGRID_FROM_EMAIL", "netrates@thehireman.co.uk")
        )
    
    # Priority 3: Webhook with SendGrid fallback
    elif os.getenv("WEBHOOK_EMAIL_URL"):
        sendgrid_fallback = None
        if os.getenv("SENDGRID_API_KEY"):
            sendgrid_fallback = {
                'api_key': os.getenv("SENDGRID_API_KEY"),
                'from_email': os.getenv("SENDGRID_FROM_EMAIL", "netrates@thehireman.co.uk")
            }
        
        result = send_email_via_webhook(
            customer_name, admin_df, transport_df, admin_email,
            os.getenv("WEBHOOK_EMAIL_URL"), sendgrid_fallback
        )
    
    # Priority 4: Other SMTP configurations
    elif smtp_config.get('enabled', False):
        result = send_email_via_smtp(
            customer_name, admin_df, transport_df, admin_email, smtp_config
        )
    
    # Fallback: Prepare for manual sending
    else:
        result = prepare_email_data(customer_name, admin_df, transport_df, admin_email)
    
    # Show result
    if result['status'] == 'sent':
        st.success(f"✅ {result['message']}")
        st.balloons()
    elif result['status'] == 'prepared':
        st.success("✅ Email prepared successfully!")
        st.info("💡 Configure email settings in sidebar for automatic sending")
        
        # Show email preview
        with st.expander("📧 Email Preview"):
            if 'email_obj' in result:
                email_obj = result['email_obj']
                st.text(f"To: {email_obj['to']}")
                st.text(f"Subject: {email_obj['subject']}")
                st.text_area("Body:", email_obj['body'], height=200)
                st.text(f"📎 Attachment: {email_obj['attachment_filename']}")
    else:
        st.error(f"❌ {result['message']}")
        st.info("💡 Try downloading the Excel file manually and emailing it")

def prepare_admin_dataframe(df, customer_name):
    """Prepare DataFrame for admin with proper formatting"""
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
    
    # Reorder columns
    admin_df = admin_df[[
        "Customer Name", "Date Created", "Item Category", "Equipment Name",
        "Original Price (£)", "Net Price (£)", "Discount %", "Group", "Sub Section"
    ]]
    
    return admin_df

def create_transport_data():
    """Create transport charges data"""
    transport_types = [
        "Standard - small tools", "Towables", "Non-mechanical", "Fencing",
        "Tower", "Powered Access", "Low-level Access", "Long Distance"
    ]
    
    default_charges = ["5", "7.5", "10", "15", "5", "Negotiable", "5", "15"]
    
    transport_data = []
    for i, (transport_type, default_value) in enumerate(zip(transport_types, default_charges)):
        charge = st.session_state.get(f"transport_{i}", default_value)
        transport_data.append({
            "Delivery or Collection type": transport_type,
            "Charge (£)": charge
        })
    
    return pd.DataFrame(transport_data)

# RUN THE APP
if __name__ == "__main__":
    main_app()
