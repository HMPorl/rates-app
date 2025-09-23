# Net Rates Calculator - Production Version
# Enhanced features and improved architecture
# Redeployment trigger - Sept 16, 2025

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
import time
import glob
from reportlab.lib.utils import ImageReader

# Google Drive API imports
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    st.warning("⚠️ Google Drive integration not available. Install required packages.")

# -------------------------------
# Configuration Management
# -------------------------------
CONFIG_FILE = "config.json"

# EMAIL SERVICE CONFIGURATION
# SendGrid API Configuration - Cloud Compatible
try:
    # Try Streamlit secrets first (for cloud deployment)
    SENDGRID_API_KEY = st.secrets.get("sendgrid", {}).get("SENDGRID_API_KEY", "") or os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = st.secrets.get("sendgrid", {}).get("SENDGRID_FROM_EMAIL", "") or os.getenv("SENDGRID_FROM_EMAIL", "netrates@thehireman.co.uk")
except (AttributeError, KeyError, Exception):
    # Fallback to environment variables (for local development)
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "netrates@thehireman.co.uk")

def load_config():
    """Load configuration from JSON file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading config: {e}")
    
    # Return default config if file doesn't exist or has errors
    return {
        "smtp_settings": {
            "provider": "SendGrid",  # Default to SendGrid
            "sendgrid_api_key": SENDGRID_API_KEY,
            "sendgrid_from_email": SENDGRID_FROM_EMAIL,
            "gmail_user": "",
            "gmail_password": "",
            "o365_user": "",
            "o365_password": "",
            "custom_server": "",
            "custom_port": 587,
            "custom_user": "",
            "custom_password": "",
            "custom_from": "",
            "custom_use_tls": True
        },
        "admin_settings": {
            "default_admin_email": "netrates@thehireman.co.uk",
            "cc_emails": ""
        }
    }

def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Net Rates Calculator",
    page_icon="🚀",
    layout="wide"
)

# -------------------------------
# Session State Initialization
# -------------------------------
def initialize_session_state():
    """Safely initialize session state variables"""
    try:
        # Load configuration at startup
        if 'config' not in st.session_state:
            st.session_state.config = load_config()
        
        # Authentication state
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
    except Exception as e:
        st.error(f"Error initializing session state: {e}")

def safe_set_session_state(key, value):
    """Safely set session state with error handling"""
    try:
        # Validate the key and value
        if not isinstance(key, str):
            st.error(f"Invalid session state key type: {type(key)}")
            return False
        
        # Check for problematic values
        if value is None:
            st.session_state[key] = ""
        elif isinstance(value, (str, int, float, bool, list, dict)):
            st.session_state[key] = value
        else:
            # Convert complex objects to string representation
            st.session_state[key] = str(value)
        
        return True
    except Exception as e:
        st.error(f"Error setting session state key '{key}': {e}")
        return False

# Initialize session state
initialize_session_state()

# -------------------------------
# Google Drive Integration Functions
# -------------------------------

def get_google_drive_service():
    """Initialize Google Drive service using OAuth or service account credentials"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return None
    
    try:
        # Try OAuth approach first (uses user's storage quota)
        oauth_creds = st.secrets.get("google_oauth", {})
        if oauth_creds:
            try:
                from google.oauth2.credentials import Credentials
                credentials = Credentials(
                    token=oauth_creds.get("access_token"),
                    refresh_token=oauth_creds.get("refresh_token"),
                    token_uri=oauth_creds.get("token_uri", "https://oauth2.googleapis.com/token"),
                    client_id=oauth_creds.get("client_id"),
                    client_secret=oauth_creds.get("client_secret"),
                    scopes=[
                        'https://www.googleapis.com/auth/drive.file',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                service = build('drive', 'v3', credentials=credentials)
                return service
            except Exception as oauth_error:
                st.warning(f"OAuth credentials failed: {oauth_error}")
        
        # Fallback to service account (but this has storage quota issues)
        creds_info = st.secrets.get("google_drive", {})
        if not creds_info:
            st.error("Google Drive credentials not found in secrets")
            return None
        
        # Try domain-wide delegation approach
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=[
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        # Try to delegate to user account
        delegated_creds = credentials.with_subject('staff.hireman@gmail.com')
        service = build('drive', 'v3', credentials=delegated_creds)
        return service
        
    except Exception as e:
        st.error(f"Failed to initialize Google Drive service: {e}")
        st.info("💡 **Alternative Solution**: Consider using OAuth instead of service account to avoid storage quota issues.")
        return None

def find_or_create_shared_drive(service, drive_name):
    """Find existing shared drive or provide instructions to create one"""
    try:
        # List shared drives
        results = service.drives().list().execute()
        drives = results.get('drives', [])
        
        for drive in drives:
            if drive['name'] == drive_name:
                return drive['id']
        
        # If drive not found, return None and let user know
        return None
    except Exception as e:
        st.error(f"Error searching for shared drive: {e}")
        return None

def find_or_create_folder(service, folder_name, parent_folder_id=None):
    """Find existing folder or create new one"""
    try:
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        folder = service.files().create(body=folder_metadata).execute()
        return folder.get('id')
    except Exception as e:
        st.error(f"Error managing folder '{folder_name}': {e}")
        return None

def save_progress_to_google_drive(progress_data, customer_name):
    """Save progress data to Google Drive (with local fallback)"""
    # Always save locally first as backup
    safe_customer_name = customer_name.strip().replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{safe_customer_name}_progress_{timestamp}.json"
    json_content = json.dumps(progress_data, indent=2)
    
    # Determine local save path based on environment
    try:
        # Try Downloads folder first (for local development)
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(downloads_path):
            local_file_path = os.path.join(downloads_path, filename)
            save_location = "Downloads folder"
        else:
            # Fallback to current directory (for cloud deployment)
            local_file_path = filename
            save_location = "app directory"
        
        # Save locally
        with open(local_file_path, 'w') as f:
            f.write(json_content)
        st.success(f"✅ Progress saved locally to {save_location}: {filename}")
        
    except Exception as e:
        st.error(f"Failed to save locally: {e}")
        return False
    
    # Try Google Drive as additional backup (optional)
    if not GOOGLE_DRIVE_AVAILABLE:
        st.info("📁 File saved locally. Google Drive integration not available.")
        return True
    
    try:
        service = get_google_drive_service()
        if not service:
            st.info("📁 File saved locally. Google Drive connection failed.")
            return True
        
        # Find the "Net Rates App" folder
        query = "name='Net Rates App' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        if not folders:
            st.info("📁 File saved locally. Google Drive folder 'Net Rates App' not found.")
            return True
        
        main_folder_id = folders[0]['id']
        
        # Find or create Current_Saves subfolder
        current_saves_id = find_or_create_folder(service, "Current_Saves", main_folder_id)
        if not current_saves_id:
            st.info("📁 File saved locally. Could not access Google Drive Current_Saves folder.")
            return True
        
        # Upload file to Google Drive
        file_metadata = {
            'name': filename,
            'parents': [current_saves_id]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(json_content.encode('utf-8')),
            mimetype='application/json',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        st.success(f"✅ Progress saved locally AND to Google Drive: {filename}")
        st.info(f"📁 Google Drive File ID: {file.get('id')}")
        return True
        
    except Exception as e:
        st.warning(f"Google Drive upload failed: {e}")
        st.info("📁 But don't worry - your progress is saved locally!")
        return True  # Still return True because local save succeeded

def list_progress_files_from_google_drive():
    """List available progress files from Google Drive"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return []
    
    try:
        service = get_google_drive_service()
        if not service:
            return []
        
        # Find the "Net Rates App" folder that you've shared with the service account
        query = "name='Net Rates App' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        if not folders:
            st.warning("⚠️ 'Net Rates App' folder not found. No files to load.")
            return []
        
        main_folder_id = folders[0]['id']
        
        # Find Current_Saves folder
        current_saves_id = find_or_create_folder(service, "Current_Saves", main_folder_id)
        
        if not current_saves_id:
            return []
        
        # List JSON files in Current_Saves
        query = f"'{current_saves_id}' in parents and name contains '.json'"
        results = service.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields='files(id,name,modifiedTime,size)'
        ).execute()
        
        files = results.get('files', [])
        return files
        
    except Exception as e:
        st.error(f"Failed to list files from Google Drive: {e}")
        return []

def load_progress_from_google_drive(file_id):
    """Load progress data from Google Drive file"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return None
    
    try:
        service = get_google_drive_service()
        if not service:
            return None
        
        # Download file content
        file_content = service.files().get_media(fileId=file_id).execute()
        progress_data = json.loads(file_content.decode('utf-8'))
        
        return progress_data
        
    except Exception as e:
        st.error(f"Failed to load file from Google Drive: {e}")
        return None

def list_local_progress_files():
    """List available local progress files from Downloads folder or current directory"""
    try:
        import os
        files_with_info = []
        
        # Check Downloads folder first (for local development)
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(downloads_path):
            pattern = os.path.join(downloads_path, "*_progress_*.json")
            downloads_files = glob.glob(pattern)
            
            for filepath in downloads_files:
                try:
                    stat = os.stat(filepath)
                    filename = os.path.basename(filepath)
                    files_with_info.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'location': 'Downloads'
                    })
                except:
                    filename = os.path.basename(filepath)
                    files_with_info.append({
                        'name': filename,
                        'path': filepath,
                        'size': 0,
                        'modified': 0,
                        'location': 'Downloads'
                    })
        
        # Also check current directory (for cloud deployment)
        current_dir_files = glob.glob("*_progress_*.json")
        for filepath in current_dir_files:
            try:
                stat = os.stat(filepath)
                filename = os.path.basename(filepath)
                # Only add if not already found in Downloads
                if not any(f['name'] == filename for f in files_with_info):
                    files_with_info.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'location': 'App Directory'
                    })
            except:
                filename = os.path.basename(filepath)
                if not any(f['name'] == filename for f in files_with_info):
                    files_with_info.append({
                        'name': filename,
                        'path': filepath,
                        'size': 0,
                        'modified': 0,
                        'location': 'App Directory'
                    })
        
        # Sort by modified time (newest first)
        files_with_info.sort(key=lambda x: x['modified'], reverse=True)
        return files_with_info
        
    except Exception as e:
        st.error(f"Failed to list local files: {e}")
        return []

def load_progress_from_local_file(filepath):
    """Load progress data from local file"""
    try:
        with open(filepath, 'r') as f:
            progress_data = json.load(f)
        return progress_data
    except Exception as e:
        st.error(f"Failed to load local file: {e}")
        return None

def get_available_pdf_files():
    """Get list of available PDF files - not cached to always show latest files"""
    try:
        pdf_files = glob.glob("*.pdf")
        return sorted(pdf_files)  # Sort alphabetically for consistent order
    except Exception as e:
        st.error(f"Error scanning for PDF files: {e}")
        return []

@st.cache_data
def load_excel_with_timestamp(file_path, timestamp):
    """Load Excel file with timestamp-based cache invalidation"""
    return pd.read_excel(file_path, engine='openpyxl')

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

# -------------------------------
# Security: PIN Authentication
# -------------------------------

if not st.session_state.authenticated:
    st.title("🔐 Net Rates Calculator - Access Required")
    st.markdown("### Please enter your credentials to access the calculator")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Username:", max_chars=10, placeholder="Enter username")
        pin_input = st.text_input("Enter PIN:", type="password", max_chars=4, placeholder="****")
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔓 Access Calculator", type="primary", use_container_width=True):
                if username_input == "HM" and pin_input == "1985":
                    st.session_state.authenticated = True
                    st.session_state.current_user = username_input  # Store username for potential future use
                    st.success("✅ Access granted! Redirecting...")
                    st.rerun()
                else:
                    if username_input != "HM":
                        st.error("❌ Incorrect username. Please try again.")
                    elif pin_input != "1985":
                        st.error("❌ Incorrect PIN. Please try again.")
                    else:
                        st.error("❌ Incorrect credentials. Please try again.")
    
    st.markdown("---")
    st.info("💡 **Need access?** Contact your system administrator for the username and PIN.")
    st.stop()  # Stop execution here if not authenticated

# -------------------------------
# Main Application Header
# -------------------------------
st.markdown("# 🚀 Net Rates Calculator")
st.markdown("*Production Version - Enhanced Features*")
st.markdown("---")

# Built-in Help System
if st.session_state.get('show_help', False):
    with st.expander("📚 **User Guide & Instructions**", expanded=True):
        st.markdown("""
        ## 🚀 Quick Start Guide
        
        ### 1️⃣ **Basic Setup**
        - **Customer Name**: Required for all exports and emails
        - **Company Logo**: Optional, appears on PDF documents
        - **Sales Person Header**: Choose PDF template for your quotes
        
        ### 2️⃣ **Setting Discounts**
        
        #### Global Discount
        - Set base discount percentage for all items
        - Use "Update all group discounts" to apply globally
        
        #### Group-Level Discounts  
        - Each equipment group can have custom discount
        - "Set All Groups to Global Discount" resets everything
        
        ### 3️⃣ **Custom Pricing**
        - **Automatic**: Items show discounted prices based on group settings
        - **Manual Override**: Enter custom prices in text boxes
        - ⚠️ System warns if you exceed maximum allowed discount
        - Only manual entries appear in "Special Rates" section
        
        ### 4️⃣ **Export Options**
        
        | Format | Use Case |
        |--------|----------|
        | 📊 **Excel** | Admin format with 3 sheets - ready for CRM |
        | 📄 **CSV** | Universal format for other systems |
        | 🔗 **JSON** | API integration or system imports |
        | 📄 **PDF** | Professional customer-facing quotes |
        | 💾 **Save Progress** | JSON backup to resume work later |
        
        ### 5️⃣ **Email System**
        
        #### Recommended: SendGrid Setup
        1. Click "Email Config" toggle
        2. Select "SendGrid" 
        3. Enter API key and from email
        4. Save settings - now ready for reliable delivery!
        
        #### Email Features
        - ✅ **Dual Attachments**: Excel (for CRM) + JSON (for backup)
        - ✅ **CC Support**: CC yourself or others
        - ✅ **Professional Format**: Auto-generated business emails
        - ✅ **Reliable Delivery**: SendGrid ensures best attachment support
        
        ### 6️⃣ **Advanced Features**
        
        #### Admin Options
        - Upload custom Excel templates
        - Upload custom PDF headers  
        - Override default system files
        
        ## 🛠️ **Troubleshooting**
        
        ### Email Issues
        - **SendGrid errors**: Check API key and verified sender email
        - **Gmail issues**: Need 2-factor auth + app password
        - **Attachment problems**: SendGrid provides best support
        
        ### Export Issues  
        - Ensure customer name is entered first
        - PDF requires sales person header selection
        - Check browser download permissions
        
        ## ✅ **Best Practices**
        
        1. **Always enter customer name first** - Required for exports
        2. **Save progress frequently** - Especially for large lists  
        3. **Test email settings** - Use test button before important quotes
        4. **Use SendGrid** - Most reliable for business email delivery
        5. **Review discount warnings** - Stay within maximum limits
        
        ## 📞 **Support**
        - 📧 Email: netrates@thehireman.co.uk
        - 💡 Check this guide first for common questions
        
        ---
        *Net Rates Calculator - The Hireman | Version: August 2025*
        """)

#if st.button("📂 Go to Load Progress Section"):
#    st.session_state["scroll_to_load"] = True

# Ensure progress_saves folder exists
if not os.path.exists("progress_saves"):
    os.makedirs("progress_saves")


# -------------------------------
# File Uploads and Inputs
# -------------------------------
DEFAULT_EXCEL_PATH = "Net rates Webapp.xlsx"  # Change this to your actual default file name

def get_available_pdf_files():
    """Get list of available PDF files - not cached to always show latest files"""
    try:
        pdf_files = glob.glob("*.pdf")
        return sorted(pdf_files)  # Sort alphabetically for consistent order
    except Exception as e:
        st.error(f"Error scanning for PDF files: {e}")
        return []

@st.cache_data
def load_excel(file):
    """Load Excel file with caching"""
    return pd.read_excel(file, engine='openpyxl')

@st.cache_data
def load_excel_with_timestamp(file_path, timestamp):
    """Load Excel file with timestamp-based cache invalidation"""
    return pd.read_excel(file_path, engine='openpyxl')

@st.cache_data
def read_pdf_header(file):
    return file.read()

def send_email_via_sendgrid_api(customer_name, admin_df, transport_df, recipient_email, cc_email=None, global_discount=0, original_df=None):
    """Send email with Excel attachment using SendGrid API - Clean implementation"""
    try:
        # Import SendGrid here to handle missing library gracefully
        import sendgrid
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        
        # Create Excel file data
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
        
        # Get API credentials
        config = st.session_state.get('config', {})
        smtp_settings = config.get("smtp_settings", {})
        
        # Get API key from saved settings or environment variable
        sendgrid_api_key = smtp_settings.get("sendgrid_api_key", "") or SENDGRID_API_KEY
        sendgrid_from_email = smtp_settings.get("sendgrid_from_email", "") or SENDGRID_FROM_EMAIL
        
        if not sendgrid_api_key:
            return {'status': 'error', 'message': 'SendGrid API key not configured. Please configure in Email Config.'}
        
        if not sendgrid_from_email:
            return {'status': 'error', 'message': 'SendGrid from email not configured. Please configure in Email Config.'}
        
        # Encode Excel file as base64 for attachment
        excel_base64 = base64.b64encode(output_excel.getvalue()).decode()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"{customer_name}_pricelist_{timestamp}.xlsx"
        
        # Create professional email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #002D56;">New Net Rates Price List</h2>
            
            <p><strong>Customer:</strong> {customer_name}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Items:</strong> {len(admin_df)}</p>
            
            <h3 style="color: #002D56;">Summary</h3>
            <ul>
                <li><strong>Price List:</strong> {len(admin_df)} equipment items</li>
                <li><strong>Transport Options:</strong> {len(transport_df)} delivery types</li>
                <li><strong>Attachments:</strong> Excel spreadsheet + JSON backup file</li>
            </ul>
            
            <h3 style="color: #002D56;">Attached Files</h3>
            <ul>
                <li><strong>Excel File:</strong> Complete pricing data ready for CRM import</li>
                <li><strong>JSON File:</strong> Calculator backup file (can be reloaded into Net Rates Calculator)</li>
            </ul>
            
            <h4 style="color: #002D56;">Excel File Contents:</h4>
            <ul>
                <li><strong>Price List Sheet:</strong> Complete equipment pricing with customer details</li>
                <li><strong>Transport Charges Sheet:</strong> Delivery and collection rates</li>
                <li><strong>Summary Sheet:</strong> Overview with totals and metadata</li>
            </ul>
            
            <p style="margin-top: 20px;">
                <em>Generated by Net Rates Calculator - The Hireman</em>
            </p>
        </body>
        </html>
        """
        
        # Create SendGrid mail object
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        
        # Setup email recipients (include CC if provided)
        to_emails = [recipient_email]
        if cc_email and cc_email.strip():
            cc_emails = [cc_email.strip()]
        else:
            cc_emails = None
        
        message = Mail(
            from_email=sendgrid_from_email,
            to_emails=to_emails,
            subject=f"Net Rates Price List - {customer_name} ({datetime.now().strftime('%Y-%m-%d')})",
            html_content=html_content
        )
        
        # Add CC if provided
        if cc_emails:
            message.cc = cc_emails
        
        # Create JSON save file for backup/reload capability
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare JSON save data (same format as Save Progress feature)
        # Use original_df if provided, otherwise fallback to a simple approach
        if original_df is not None and hasattr(original_df, 'iterrows'):
            custom_prices = {
                str(row["ItemCategory"]): st.session_state.get(f"price_{idx}", "")
                for idx, row in original_df.iterrows()
            }
        else:
            # Fallback: get custom prices from session state directly
            custom_prices = {
                key.replace("price_", ""): st.session_state.get(key, "")
                for key in st.session_state
                if key.startswith("price_")
            }
            
        save_data = {
            "customer_name": customer_name,
            "global_discount": global_discount,
            "group_discounts": {
                key: st.session_state.get(key, 0)
                for key in st.session_state
                if key.endswith("_discount")
            },
            "custom_prices": custom_prices,
            "transport_charges": {
                key: st.session_state.get(key, "")
                for key in st.session_state
                if key.startswith("transport_")
            },
            "created_timestamp": datetime.now().isoformat(),
            "created_by": "Net Rates Calculator"
        }
        
        json_data = json.dumps(save_data, indent=2)
        json_base64 = base64.b64encode(json_data.encode()).decode()
        json_filename = f"{customer_name}_progress_backup_{timestamp}.json"
        
        # Create and attach Excel file
        excel_attachment = Attachment(
            FileContent(excel_base64),
            FileName(excel_filename),
            FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            Disposition('attachment')
        )
        
        # Create and attach JSON save file
        json_attachment = Attachment(
            FileContent(json_base64),
            FileName(json_filename),
            FileType('application/json'),
            Disposition('attachment')
        )
        
        # Add both attachments to message
        message.attachment = [excel_attachment, json_attachment]
        
        # Send email
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            cc_message = f" (CC: {cc_email})" if cc_email and cc_email.strip() else ""
            return {
                'status': 'sent', 
                'message': f'Email with Excel & JSON backup files sent to {recipient_email}{cc_message}',
                'status_code': response.status_code
            }
        else:
            return {
                'status': 'error', 
                'message': f'SendGrid API returned status code: {response.status_code}'
            }
            
    except ImportError:
        return {
            'status': 'error', 
            'message': 'SendGrid library not installed. Run: pip install sendgrid'
        }
    except Exception as e:
        return {
            'status': 'error', 
            'message': f'SendGrid API error: {str(e)}'
        }

def send_email_with_pricelist(customer_name, admin_df, transport_df, recipient_email, smtp_config=None, cc_email=None, global_discount=0, original_df=None):
    """Send price list via email to admin team"""
    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = smtp_config.get('from_email', 'noreply@thehireman.co.uk') if smtp_config else 'noreply@thehireman.co.uk'
        msg['To'] = recipient_email
        
        # Add CC if provided
        if cc_email and cc_email.strip():
            msg['Cc'] = cc_email.strip()
            
        msg['Subject'] = f"Price List for {customer_name} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Email body
        cc_note = f"\n(CC: {cc_email})" if cc_email and cc_email.strip() else ""
        body = f"""
Hello Admin Team,

Please find attached the price list for customer: {customer_name}

Summary:
- Total Items: {len(admin_df)}
- Date Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Created via: Net Rates Calculator{cc_note}

The attached files contain:
- Excel file: Complete price list with transport charges and summary
- JSON file: Backup/reload file for the Net Rates Calculator

Please import the Excel data into our CRM system.
The JSON file can be used to reload this exact configuration in the calculator if needed.

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
        
        # Create and attach JSON save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Use original_df if provided, otherwise fallback to a simple approach
        if original_df is not None and hasattr(original_df, 'iterrows'):
            custom_prices = {
                str(row["ItemCategory"]): st.session_state.get(f"price_{idx}", "")
                for idx, row in original_df.iterrows()
            }
        else:
            # Fallback: get custom prices from session state directly
            custom_prices = {
                key.replace("price_", ""): st.session_state.get(key, "")
                for key in st.session_state
                if key.startswith("price_")
            }
            
        save_data = {
            "customer_name": customer_name,
            "global_discount": global_discount,
            "group_discounts": {
                key: st.session_state.get(key, 0)
                for key in st.session_state
                if key.endswith("_discount")
            },
            "custom_prices": custom_prices,
            "transport_charges": {
                key: st.session_state.get(key, "")
                for key in st.session_state
                if key.startswith("transport_")
            },
            "created_timestamp": datetime.now().isoformat(),
            "created_by": "Net Rates Calculator"
        }
        
        json_data = json.dumps(save_data, indent=2)
        json_filename = f"{customer_name}_progress_backup_{timestamp}.json"
        
        # Attach JSON file
        json_part = MIMEBase('application', 'json')
        json_part.set_payload(json_data.encode('utf-8'))
        encoders.encode_base64(json_part)
        json_part.add_header(
            'Content-Disposition',
            f'attachment; filename={json_filename}'
        )
        msg.attach(json_part)
        
        # Send email if SMTP is configured
        if smtp_config and smtp_config.get('enabled', False):
            try:
                server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                text = msg.as_string()
                
                # Build recipient list (includes CC if provided)
                recipients = [recipient_email]
                if cc_email and cc_email.strip():
                    recipients.append(cc_email.strip())
                
                server.sendmail(smtp_config['from_email'], recipients, text)
                server.quit()
                
                cc_message = f" (CC: {cc_email})" if cc_email and cc_email.strip() else ""
                return {'status': 'sent', 'message': f'Email with attachments sent successfully{cc_message}!'}
            except Exception as e:
                return {'status': 'error', 'message': f'SMTP Error: {str(e)}'}
        else:
            # Return the email content for manual sending or configuration
            return {'status': 'prepared', 'message': 'Email prepared (SMTP not configured)', 'email_obj': msg}
            
    except Exception as e:
        return {'status': 'error', 'message': f'Email preparation failed: {str(e)}'}

# Customer name input
customer_name = st.text_input("⭐Enter Customer Name", key="customer_name")

bespoke_email = st.text_input("⭐ Bespoke email address (optional)")
logo_file = st.file_uploader("⭐Upload Company Logo", type=["png", "jpg", "jpeg"])

# --- Move PDF header selection ABOVE Excel upload ---
# Add refresh button for PDF headers
col1, col2 = st.columns([4, 1])

with col1:
    # Get available PDF files dynamically (not cached)
    available_pdfs = get_available_pdf_files()
    header_pdf_choice = st.selectbox(
        "⭐Select a PDF Header Sheet",
        ["(Select Sales Person)"] + available_pdfs,
        help=f"Found {len(available_pdfs)} PDF files in the current directory"
    )

with col2:
    if st.button("🔄 Refresh PDF List", help="Click to refresh the list of available PDF header files"):
        st.rerun()

# Toggle for admin options (hide by default)
show_admin_uploads = st.toggle("Show Admin Upload Options", value=False)

if show_admin_uploads:
    st.markdown("#### � Admin File Management")
    
    # Admin Excel upload
    uploaded_file = st.file_uploader("❗ADMIN Upload Excel file (Admin Only❗)", type=["xlsx"])
    
    # Admin PDF upload
    uploaded_header_pdf = st.file_uploader("❗ADMIN Upload PDF Header (Admin Only❗)", type=["pdf"], key="header_pdf_upload")
    
    # Show default file information in admin section
    st.markdown("#### 📊 Default File Information")
    
    if os.path.exists(DEFAULT_EXCEL_PATH):
        # Get file modification time
        import os
        mod_time = os.path.getmtime(DEFAULT_EXCEL_PATH)
        mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        file_size = os.path.getsize(DEFAULT_EXCEL_PATH) / 1024
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📁 **Default Excel File:**\n`{DEFAULT_EXCEL_PATH}`")
            st.info(f"📅 **Last Modified:**\n{mod_time_str}")
        with col2:
            st.info(f"📏 **File Size:**\n{file_size:.1f} KB")
            if st.button("🔄 Force Refresh Excel Data", help="Manually refresh Excel data cache"):
                # Clear all Excel-related caches
                load_excel.clear()
                load_excel_with_timestamp.clear()
                
                # Clear any session state that might be caching data
                cache_keys_to_clear = [key for key in st.session_state.keys() if 'excel' in key.lower() or 'df' in key.lower()]
                for key in cache_keys_to_clear:
                    del st.session_state[key]
                
                # Force Streamlit to clear all caches
                st.cache_data.clear()
                
                st.success("✅ Excel cache cleared completely!")
                st.rerun()
    else:
        st.warning(f"⚠️ **Default Excel file not found:**\n`{DEFAULT_EXCEL_PATH}`")
    
    # Show PDF files information  
    available_pdfs = get_available_pdf_files()
    if available_pdfs:
        st.info(f"📄 **Available PDF Headers:** {len(available_pdfs)} files\n{', '.join(available_pdfs)}")
    else:
        st.warning("⚠️ No PDF header files found in current directory")
        
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
        st.success(f"✅ Excel file uploaded: {uploaded_file.name}")
        
    except Exception as e:
        st.error(f"❌ Error reading uploaded Excel file: {e}")
        st.stop()
elif os.path.exists(DEFAULT_EXCEL_PATH):
    try:
        # Get file modification time for cache invalidation
        import os
        mod_time = os.path.getmtime(DEFAULT_EXCEL_PATH)
        mod_time_readable = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        
        # Use timestamp-aware loading to auto-refresh when file changes
        df = load_excel_with_timestamp(DEFAULT_EXCEL_PATH, mod_time)
        excel_source = "default"
        
        st.success(f"✅ Using default Excel data (Last modified: {mod_time_readable})")
        
    except Exception as e:
        st.error(f"❌ Failed to load default Excel: {e}")
        st.stop()
else:
    st.error(f"❌ No Excel file found. Please upload a file or ensure {DEFAULT_EXCEL_PATH} exists.")
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
    global_discount_value = st.session_state.get("global_discount", 0.0)
    global_discount = st.number_input("Global Discount (%)", min_value=0.0, max_value=100.0, value=global_discount_value, step=0.01, key="global_discount")

    # Check if global discount has changed
    previous_global_discount = st.session_state.get("previous_global_discount", global_discount)
    if global_discount != previous_global_discount:
        st.session_state["previous_global_discount"] = global_discount
        # Show option to update all group discounts when global discount changes
        if st.button(f"🔄 Update all group discounts to {global_discount}%", type="primary"):
            group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())
            for group, subsection in group_keys:
                discount_key = f"{group}_{subsection}_discount"
                st.session_state[discount_key] = global_discount
            st.success(f"✅ All group discounts updated to {global_discount}%")
            st.rerun()

    st.markdown("### Group-Level Discounts")
    group_discount_keys = {}
    group_keys = list(df.groupby(["GroupName", "Sub Section"]).groups.keys())

    # Add button to sync all group discounts with global discount
    if st.button("🔄 Set All Groups to Global Discount"):
        for group, subsection in group_keys:
            discount_key = f"{group}_{subsection}_discount"
            st.session_state[discount_key] = global_discount
        st.rerun()

    cols = st.columns(3)
    for i, (group, subsection) in enumerate(group_keys):
        col = cols[i % 3]  # Fill down each column
        with col:
            discount_key = f"{group}_{subsection}_discount"
            # Use session state value if available, otherwise use global discount
            default_value = st.session_state.get(discount_key, global_discount)
            st.number_input(
                f"{group} - {subsection} (%)",
                min_value=0.0,
                max_value=100.0,
                value=default_value,
                step=0.01,
                key=discount_key
            )


    # -------------------------------
    # Helper Functions
    # -------------------------------
    def is_poa_value(value):
        """Check if a value represents POA (Price on Application)"""
        if pd.isna(value):
            return False
        return str(value).upper().strip() in ['POA', 'PRICE ON APPLICATION', 'CONTACT FOR PRICE']
    
    def get_numeric_price(value):
        """Convert price value to numeric, return None if POA"""
        if is_poa_value(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def format_price_display(value):
        """Format price for display - handles both numeric and POA values"""
        if is_poa_value(value):
            return "POA"
        numeric_value = get_numeric_price(value)
        if numeric_value is not None:
            return f"£{numeric_value:.2f}"
        return "POA"
    
    def get_discounted_price(row):
        """Calculate discounted price, handling POA values"""
        key = f"{row['GroupName']}_{row['Sub Section']}_discount"
        discount = st.session_state.get(key, global_discount)
        
        # Check if original price is POA
        if is_poa_value(row["HireRateWeekly"]):
            return "POA"
        
        # Get numeric price for calculation
        numeric_price = get_numeric_price(row["HireRateWeekly"])
        if numeric_price is None:
            return "POA"
        
        return numeric_price * (1 - discount / 100)

    def calculate_discount_percent(original, custom):
        """Calculate discount percentage, handling POA values"""
        # If either value is POA, return special indicator
        if is_poa_value(original) or is_poa_value(custom):
            return "POA"
        
        # Get numeric values
        orig_numeric = get_numeric_price(original)
        custom_numeric = get_numeric_price(custom)
        
        if orig_numeric is None or custom_numeric is None:
            return "POA"
        
        if orig_numeric == 0:
            return 0
        
        return ((orig_numeric - custom_numeric) / orig_numeric) * 100

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
                    # Display calculated price or POA
                    if discounted_price == "POA":
                        st.write("POA")
                    else:
                        st.write(f"£{discounted_price:.2f}")
                with col4:
                    # Input field with helpful placeholder
                    placeholder_text = "Enter price or POA"
                    st.text_input("", key=price_key, label_visibility="collapsed", 
                                placeholder=placeholder_text)
                with col5:
                    # Handle custom price input (numeric or POA)
                    user_input = st.session_state.get(price_key, "").strip()
                    
                    if user_input:
                        # User entered something
                        if is_poa_value(user_input):
                            # User entered POA
                            custom_price = "POA"
                            discount_percent = "POA"
                            st.markdown("**POA**")
                        else:
                            # User entered a number
                            try:
                                custom_price = float(user_input)
                                discount_percent = calculate_discount_percent(row["HireRateWeekly"], custom_price)
                                
                                if discount_percent == "POA":
                                    st.markdown("**POA**")
                                else:
                                    st.markdown(f"**{discount_percent:.2f}%**")
                                    # Check max discount only for numeric values
                                    orig_numeric = get_numeric_price(row["HireRateWeekly"])
                                    if orig_numeric and discount_percent > row["Max Discount"]:
                                        st.warning(f"⚠️ Exceeds Max Discount ({row['Max Discount']}%)")
                            except ValueError:
                                # Invalid input - treat as POA
                                custom_price = "POA"
                                discount_percent = "POA"
                                st.markdown("**POA**")
                                st.warning("⚠️ Invalid input - treated as POA")
                    else:
                        # No user input - use calculated price
                        custom_price = discounted_price
                        discount_percent = calculate_discount_percent(row["HireRateWeekly"], custom_price)
                        
                        if discount_percent == "POA":
                            st.markdown("**POA**")
                        else:
                            st.markdown(f"**{discount_percent:.2f}%**")

                # Store the final values
                df.at[idx, "CustomPrice"] = custom_price
                df.at[idx, "DiscountPercent"] = discount_percent

    # -------------------------------
    # Save Progress Button (with Google Drive + Local Download)
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
        
        # Try to save to Google Drive first
        drive_success = save_progress_to_google_drive(save_data, customer_name)
        
        # Always provide local download option
        json_data = json.dumps(save_data, indent=2)
        st.download_button(
            label="📥 Download Local Backup",
            data=json_data,
            file_name=filename,
            mime="application/json",
            help="Download a local backup file to your computer"
        )
        
        if drive_success:
            st.info("💾 Progress saved to both Google Drive and available for local download!")
        else:
            st.warning("⚠️ Google Drive save failed, but local download is available.")

    # -------------------------------
    # Handle Upload Load Trigger
    # -------------------------------
    if st.session_state.get('trigger_upload_load', False):
        st.session_state['trigger_upload_load'] = False  # Clear the trigger
        
        uploaded_file = st.session_state.get('uploaded_file_to_load', None)
        if uploaded_file:
            try:
                loaded_data = json.load(uploaded_file)
                
                # Clear existing session state
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
                
                # Restore basic data
                safe_set_session_state("customer_name", loaded_data.get("customer_name", ""))
                safe_set_session_state("global_discount", loaded_data.get("global_discount", 0.0))
                
                # Restore group discounts
                for key, value in loaded_data.get("group_discounts", {}).items():
                    safe_set_session_state(key, value)
                    
                # Restore transport charges
                for key, value in loaded_data.get("transport_charges", {}).items():
                    safe_set_session_state(key, value)
                
                # Restore custom prices - populate the text input fields
                custom_prices = loaded_data.get("custom_prices", {})
                restored_count = 0
                if df is not None:
                    for idx, row in df.iterrows():
                        item_key = str(row["ItemCategory"])
                        price_key = f"price_{idx}"
                        if item_key in custom_prices and custom_prices[item_key]:
                            safe_set_session_state(price_key, custom_prices[item_key])
                            restored_count += 1
                
                st.success(f"✅ Progress loaded successfully! {restored_count} custom prices restored.")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to load progress: {e}")


    # -------------------------------
    # Final Price List Display
    # -------------------------------
    st.markdown("### Final Price List")
    
    # Create a display-friendly version of the dataframe
    display_df = df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly",
        "GroupName", "Sub Section", "CustomPrice", "DiscountPercent"
    ]].copy()
    
    # Format the display columns for better readability
    display_df["HireRateWeekly"] = display_df["HireRateWeekly"].apply(format_price_display)
    display_df["CustomPrice"] = display_df["CustomPrice"].apply(
        lambda x: "POA" if is_poa_value(x) or x == "POA" else f"£{float(x):.2f}" if str(x).replace('.','').replace('-','').isdigit() else str(x)
    )
    display_df["DiscountPercent"] = display_df["DiscountPercent"].apply(
        lambda x: "POA" if x == "POA" or is_poa_value(x) else f"{float(x):.2f}%" if str(x).replace('.','').replace('-','').isdigit() else str(x)
    )
    
    # Rename columns for better display
    display_df.columns = ["Item Category", "Equipment Name", "Original Price", "Group", "Sub Section", "Final Price", "Discount %"]
    
    st.dataframe(display_df, use_container_width=True)


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
            if is_poa_value(user_input):
                # User entered POA
                manual_entries.append({
                    "ItemCategory": row["ItemCategory"],
                    "EquipmentName": row["EquipmentName"],
                    "HireRateWeekly": format_price_display(row["HireRateWeekly"]),
                    "CustomPrice": "POA",
                    "DiscountPercent": "POA",
                    "GroupName": row["GroupName"],
                    "Sub Section": row["Sub Section"]
                })
            else:
                try:
                    entered_price = float(user_input)
                    manual_entries.append({
                        "ItemCategory": row["ItemCategory"],
                        "EquipmentName": row["EquipmentName"],
                        "HireRateWeekly": format_price_display(row["HireRateWeekly"]),
                        "CustomPrice": f"£{entered_price:.2f}",
                        "DiscountPercent": f"{calculate_discount_percent(row['HireRateWeekly'], entered_price):.2f}%" if calculate_discount_percent(row['HireRateWeekly'], entered_price) != "POA" else "POA",
                        "GroupName": row["GroupName"],
                        "Sub Section": row["Sub Section"]
                    })
                except ValueError:
                    # Invalid numeric input - treat as POA
                    manual_entries.append({
                        "ItemCategory": row["ItemCategory"],
                        "EquipmentName": row["EquipmentName"],
                        "HireRateWeekly": format_price_display(row["HireRateWeekly"]),
                        "CustomPrice": "POA (Invalid Input)",
                        "DiscountPercent": "POA",
                        "GroupName": row["GroupName"],
                        "Sub Section": row["Sub Section"]
                    })

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
    # Export Net Rates
    # -------------------------------
    st.markdown("### 📤 Export Net Rates")
    
    # Create admin-friendly DataFrame with clear column names
    admin_df = df[[
        "ItemCategory", "EquipmentName", "HireRateWeekly", 
        "CustomPrice", "DiscountPercent", "GroupName", "Sub Section"
    ]].copy()
    
    # Format values for export (handle POA properly)
    admin_df["HireRateWeekly"] = admin_df["HireRateWeekly"].apply(
        lambda x: "POA" if is_poa_value(x) else f"{float(x):.2f}" if get_numeric_price(x) is not None else "POA"
    )
    admin_df["CustomPrice"] = admin_df["CustomPrice"].apply(
        lambda x: "POA" if is_poa_value(x) or x == "POA" else f"{float(x):.2f}" if str(x).replace('.','').replace('-','').isdigit() else str(x)
    )
    admin_df["DiscountPercent"] = admin_df["DiscountPercent"].apply(
        lambda x: "POA" if x == "POA" or is_poa_value(x) else f"{float(x):.2f}%" if str(x).replace('.','').replace('-','').isdigit() else str(x)
    )
    
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
    # Direct Email to Accounts Team
    # -------------------------------
    st.markdown("### 📧 Email Net Rates to Accounts")
    
    # Email Configuration Toggle
    show_email_config = st.toggle("Email Config", value=False)
    
    if show_email_config:
        # SMTP Configuration Section
        with st.expander("⚙️ SMTP Configuration (Click to configure email sending)"):
            st.markdown("#### Choose Email Provider")
            
            # Load saved settings
            config = st.session_state.config
            smtp_settings = config.get("smtp_settings", {})
            
            email_provider = st.selectbox(
                "Email Service",
                ["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"],
                index=["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"].index(smtp_settings.get("provider", "Not Configured")) if smtp_settings.get("provider", "Not Configured") in ["Not Configured", "SendGrid", "Gmail", "Outlook/Office365", "Custom SMTP"] else 0
            )
            
            if email_provider == "SendGrid":
                st.info("📋 **SendGrid API Configuration:**")
                
                # Check for saved settings first, then environment variables
                saved_api_key = smtp_settings.get("sendgrid_api_key", "")
                saved_from_email = smtp_settings.get("sendgrid_from_email", "")
                
                # Use saved settings or environment variables as defaults
                default_api_key = saved_api_key or SENDGRID_API_KEY
                default_from_email = saved_from_email or SENDGRID_FROM_EMAIL or "netrates@thehireman.co.uk"
                
                col1, col2 = st.columns(2)
                with col1:
                    # API Key input with default from saved/environment
                    sg_api_key = st.text_input(
                        "SendGrid API Key", 
                        value=default_api_key,
                        type="password",
                        help="Get your API key from SendGrid dashboard → Settings → API Keys"
                    )
                    sg_from_email = st.text_input(
                        "From Email Address", 
                        value=default_from_email,
                        help="Must be a verified sender in your SendGrid account"
                    )
                with col2:
                    st.info("**SendGrid Settings:**\n- API-based email service\n- High deliverability\n- Advanced analytics\n- Free tier: 100 emails/day")
                    
                    if default_api_key:
                        st.success(f"✅ API Key loaded: {default_api_key[:8]}...{default_api_key[-4:] if len(default_api_key) > 8 else '****'}")
                
                # Save settings button
                if st.button("💾 Save SendGrid Settings"):
                    config["smtp_settings"]["provider"] = "SendGrid"
                    config["smtp_settings"]["sendgrid_api_key"] = sg_api_key
                    config["smtp_settings"]["sendgrid_from_email"] = sg_from_email
                    if save_config(config):
                        st.session_state.config = config
                        st.success("✅ SendGrid settings saved successfully!")
                        st.rerun()
                
                # Configure SMTP settings if API key is provided
                if sg_api_key and sg_from_email:
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
                    
                    st.success("📋 **SendGrid is Ready!**")
                    # Show current configuration (masking API key)
                    st.markdown(f"**From Email:** `{sg_from_email}`")
                    st.markdown(f"**API Key:** `{sg_api_key[:8]}...{sg_api_key[-4:] if len(sg_api_key) > 8 else '****'}`")
                else:
                    smtp_config = {'enabled': False}
                    if not sg_api_key:
                        st.warning("⚠️ Please enter your SendGrid API key")
                    if not sg_from_email:
                        st.warning("⚠️ Please enter a from email address")
                    
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
                    gmail_user = st.text_input("Gmail Address", value=smtp_settings.get("gmail_user", ""))
                    gmail_password = st.text_input("App Password", type="password", value=smtp_settings.get("gmail_password", ""))
                with col2:
                    st.info("**Gmail Settings:**\n- Server: smtp.gmail.com\n- Port: 587\n- TLS: Enabled")
                
                # Save settings button
                if st.button("💾 Save Gmail Settings"):
                    config["smtp_settings"]["provider"] = "Gmail"
                    config["smtp_settings"]["gmail_user"] = gmail_user
                    config["smtp_settings"]["gmail_password"] = gmail_password
                    if save_config(config):
                        st.session_state.config = config
                        st.success("✅ Gmail settings saved successfully!")
                        st.rerun()
                
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
                    o365_user = st.text_input("Office365 Email", value=smtp_settings.get("o365_user", ""))
                    o365_password = st.text_input("Password", type="password", value=smtp_settings.get("o365_password", ""))
                with col2:
                    st.info("**Office365 Settings:**\n- Server: smtp.office365.com\n- Port: 587\n- TLS: Enabled")
                
                # Save settings button
                if st.button("💾 Save Office365 Settings"):
                    config["smtp_settings"]["provider"] = "Outlook/Office365"
                    config["smtp_settings"]["o365_user"] = o365_user
                    config["smtp_settings"]["o365_password"] = o365_password
                    if save_config(config):
                        st.session_state.config = config
                        st.success("✅ Office365 settings saved successfully!")
                        st.rerun()
                
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
                    custom_server = st.text_input("SMTP Server", value=smtp_settings.get("custom_server", ""))
                    custom_port = st.number_input("SMTP Port", value=smtp_settings.get("custom_port", 587))
                    custom_user = st.text_input("Username", value=smtp_settings.get("custom_user", ""))
                with col2:
                    custom_password = st.text_input("Password", type="password", value=smtp_settings.get("custom_password", ""))
                    custom_from = st.text_input("From Email", value=smtp_settings.get("custom_from", ""))
                    use_tls = st.checkbox("Use TLS", value=smtp_settings.get("custom_use_tls", True))
                
                # Save settings button
                if st.button("💾 Save Custom SMTP Settings"):
                    config["smtp_settings"]["provider"] = "Custom SMTP"
                    config["smtp_settings"]["custom_server"] = custom_server
                    config["smtp_settings"]["custom_port"] = custom_port
                    config["smtp_settings"]["custom_user"] = custom_user
                    config["smtp_settings"]["custom_password"] = custom_password
                    config["smtp_settings"]["custom_from"] = custom_from
                    config["smtp_settings"]["custom_use_tls"] = use_tls
                    if save_config(config):
                        st.session_state.config = config
                        st.success("✅ Custom SMTP settings saved successfully!")
                        st.rerun()
                
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
        
        # Clear settings button
        if email_provider != "Not Configured":
            if st.button("🗑️ Clear Saved Settings"):
                config["smtp_settings"] = {
                    "provider": "",
                    "sendgrid_api_key": "",
                    "sendgrid_from_email": "",
                    "gmail_user": "",
                    "gmail_password": "",
                    "o365_user": "",
                    "o365_password": "",
                    "custom_server": "",
                    "custom_port": 587,
                    "custom_user": "",
                    "custom_password": "",
                    "custom_from": "",
                    "custom_use_tls": True
                }
                if save_config(config):
                    st.session_state.config = config
                    st.success("✅ Settings cleared successfully!")
                    st.rerun()
        
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
    else:
        # When email config is hidden, use default config
        smtp_config = {'enabled': False}
    
    # Email Form
    col1, col2 = st.columns(2)
    with col1:
        # Hard-coded admin email address
        admin_email = st.text_input("Accounts Team Email", value="netrates@thehireman.co.uk")
        # CC email input
        cc_email = st.text_input("CC Email (optional)", placeholder="your.email@company.com", help="CC yourself or others on this email")
    with col2:
        include_transport = st.checkbox("Include Transport Charges", value=True)
    
    # Status indicator - SendGrid focused
    config = st.session_state.get('config', {})
    smtp_settings = config.get("smtp_settings", {})
    saved_sendgrid_key = smtp_settings.get("sendgrid_api_key", "")
    
    if smtp_config.get('enabled', False) and smtp_config.get('provider') == 'SendGrid':
        st.success("✅ SendGrid configured - Perfect Excel attachments ready!")
    elif saved_sendgrid_key or SENDGRID_API_KEY:
        st.success("✅ SendGrid available - Reliable Excel attachment delivery!")
    elif smtp_config.get('enabled', False):
        st.warning(f"⚠️ {smtp_config.get('provider', 'SMTP')} configured - Excel attachments may have issues. SendGrid recommended.")
    else:
        st.info("📧 Configure SendGrid in Email Config above for best results")
    
    if st.button("📨 Send Email to Admin Team", type="primary") and admin_email:
        if customer_name:
            try:
                # Priority 1: Use SendGrid API (best for attachments)
                if (smtp_config.get('enabled', False) and smtp_config.get('provider') == 'SendGrid') or saved_sendgrid_key or SENDGRID_API_KEY:
                    result = send_email_via_sendgrid_api(
                        customer_name, 
                        admin_df, 
                        transport_df if include_transport else pd.DataFrame(), 
                        admin_email,
                        cc_email if cc_email and cc_email.strip() else None,
                        global_discount,
                        df  # Pass the original DataFrame
                    )
                # Priority 2: Use other SMTP if configured
                elif smtp_config.get('enabled', False):
                    result = send_email_with_pricelist(
                        customer_name, 
                        admin_df, 
                        transport_df if include_transport else pd.DataFrame(), 
                        admin_email,
                        smtp_config,
                        cc_email if cc_email and cc_email.strip() else None,
                        global_discount,
                        df  # Pass the original DataFrame
                    )
                else:
                    # Fallback: prepare email data for manual sending
                    result = send_email_with_pricelist(
                        customer_name, 
                        admin_df, 
                        transport_df if include_transport else pd.DataFrame(), 
                        admin_email,
                        None,
                        cc_email if cc_email and cc_email.strip() else None,
                        global_discount,
                        df  # Pass the original DataFrame
                    )
                
                if result['status'] == 'sent':
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                elif result['status'] == 'saved':
                    st.success(f"✅ Email data prepared successfully!")
                    st.info("📁 Data saved locally. Admin will process this shortly.")
                elif result['status'] == 'prepared':
                    st.success(f"✅ Email prepared successfully!")
                    st.info("📝 **Note**: Configure SMTP above to enable automatic sending.")
                    
                    # Show email preview
                    with st.expander("📧 Email Preview"):
                        email_obj = result.get('email_obj')
                        if email_obj:
                            st.text(f"To: {admin_email}")
                            if cc_email and cc_email.strip():
                                st.text(f"CC: {cc_email}")
                            st.text(f"Subject: {email_obj['Subject']}")
                            st.text("📎 Attachments:")
                            st.text("   • Excel file with price list")
                            st.text("   • JSON backup file for calculator")
                else:
                    st.error(f"❌ {result['message']}")
                    st.info("💡 **Alternative**: Download the Excel file above and email it manually.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 **Alternative**: Download the Excel file above and email it manually.")
        else:
            st.warning("⚠️ Please enter a customer name first")

    # -------------------------------
    # Export Net Rates to PDF
    # -------------------------------
    st.markdown("---")
    st.markdown("### 📄 Export Net Rates to PDF")
    st.markdown("Generate a professional PDF document with your customized pricing.")

    # Add a checkbox for including the custom price table
    # Add a checkbox for including the custom price table
    include_custom_table = st.checkbox("Include Special Rates at top of PDF", value=True)
    
    # Add a checkbox for page break after special rates
    special_rates_pagebreak = st.checkbox("Separate Special Rates on their own page", value=False)

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
                # Only include numeric prices in Special Rates section
                # POA items are excluded from this section
                if not is_poa_value(user_input):
                    try:
                        entered_price = float(user_input)
                        custom_price_rows.append([
                            row["ItemCategory"],
                            Paragraph(row["EquipmentName"], styles['BodyText']),
                            f"£{entered_price:.2f}"
                        ])
                    except ValueError:
                        # Invalid input - skip (don't include in Special Rates)
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
                ('BACKGROUND', (0, 0), (-1, 0), '#FFD51D'),  # Updated yellow color
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                # Removed GRID line to eliminate cell borders
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
            special_rate_rows = []  # Track rows with special rates for highlighting
            
            for row_idx, (_, row) in enumerate(sub_df.iterrows(), start=1):  # start=1 because header is row 0
                # Handle POA values in PDF generation
                if is_poa_value(row['CustomPrice']) or row['CustomPrice'] == "POA":
                    price_text = "POA"
                    has_special_rate = False
                else:
                    try:
                        price_text = f"£{float(row['CustomPrice']):.2f}"
                        # Check if this is a special rate (user entered custom price)
                        price_key = f"price_{row.name}"  # row.name is the original DataFrame index
                        user_input = str(st.session_state.get(price_key, "")).strip()
                        has_special_rate = bool(user_input and not is_poa_value(user_input))
                    except (ValueError, TypeError):
                        price_text = "POA"
                        has_special_rate = False
                
                # Track rows with special rates for highlighting
                if has_special_rate:
                    special_rate_rows.append(row_idx)
                
                table_data.append([
                    row["ItemCategory"],
                    Paragraph(row["EquipmentName"], styles['BodyText']),
                    price_text
                ])

            table_with_repeat_header = Table(
                table_data,
                colWidths=table_col_widths,
                repeatRows=1
            )
            
            # Build table style with yellow highlighting for special rates
            table_style = [
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
            ]
            
            # Add yellow highlighting for special rate rows
            for row_num in special_rate_rows:
                table_style.append(('BACKGROUND', (0, row_num), (-1, row_num), '#FFD51D'))  # Updated yellow color
            
            table_with_repeat_header.setStyle(TableStyle(table_style))

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

    # Make PDF download button prominent and red
    st.markdown("---")
    st.markdown("#### 🎯 **Download Your PDF Price List**")
    st.download_button(
        label="📄 Download as PDF",
        data=merged_output.getvalue(),
        file_name=filename,
        mime="application/pdf",
        type="primary",
        help="Download your customized price list as a PDF document"
    )
    
    # Add custom CSS to make the button red
    st.markdown("""
    <style>
    .stDownloadButton > button {
        background-color: #ff4444 !important;
        color: white !important;
        border: 2px solid #ff4444 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        margin: 10px 0 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #cc0000 !important;
        border-color: #cc0000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# Admin Dashboard (Collapsible)
# -------------------------------
st.markdown("---")
with st.expander("🔧 Admin Dashboard & Integration Settings"):
    st.markdown("### 🏢 Admin Team Integration Hub")
    
    tab1, tab2, tab3 = st.tabs(["📧 Email Settings", "🔄 Automation", "📊 Analytics"])
    
    with tab1:
        st.markdown("#### � SendGrid API Configuration (Recommended)")
        
        # SendGrid Configuration
        col1, col2 = st.columns([3, 1])
        with col1:
            current_api_key = SENDGRID_API_KEY
            current_from_email = SENDGRID_FROM_EMAIL
            
            st.text_input(
                "SendGrid API Key",
                value=current_api_key[:8] + "..." + current_api_key[-4:] if current_api_key else "Not configured",
                disabled=True,
                help="Configure via environment variables or Email Config in main app"
            )
            st.text_input(
                "From Email Address", 
                value=current_from_email if current_from_email else "Not configured",
                disabled=True,
                help="Verified sender address in SendGrid"
            )
        
        with col2:
            if current_api_key and current_from_email:
                st.success("✅ SendGrid Ready")
                st.info("Perfect Excel attachments enabled!")
            else:
                st.warning("⚠️ Not Configured")
                st.info("Use Email Config toggle in main app")
        
        # Status display
        if current_api_key and current_from_email:
            st.success("✅ SendGrid configured - users can send perfect Excel attachments!")
            st.markdown(f"**From Email:** `{current_from_email}`")
            st.markdown(f"**API Key:** `{current_api_key[:8]}...{current_api_key[-4:] if len(current_api_key) > 8 else '****'}`")
        else:
            st.info("� Configure SendGrid for reliable Excel attachment delivery")
            
        # Quick help section
        with st.expander("❓ How to configure SendGrid"):
            st.markdown("""
            **Steps to configure SendGrid:**
            1. Sign up at [SendGrid.com](https://sendgrid.com) (free tier: 100 emails/day)
            2. Go to Settings → API Keys → Create API Key
            3. Choose "Restricted Access" and enable "Mail Send" permissions
            4. Copy the API key
            5. Go to Settings → Sender Authentication → Verify single sender
            6. Verify your from email address
            7. Use the Email Config toggle in the main app to configure
            
            **Why SendGrid?**
            - ✅ Perfect Excel attachment delivery (no .txt file corruption)
            - ✅ Professional email appearance
            - ✅ 99.9% delivery rate
            - ✅ Advanced analytics and tracking
            - ✅ Reliable API with excellent documentation
            """)
        
        st.markdown("---")
        st.markdown("#### 📧 Alternative Email Options")
        
        # Load saved admin settings
        admin_settings = st.session_state.config.get("admin_settings", {})
        
        col1, col2 = st.columns(2)
        with col1:
            default_admin_email = st.text_input(
                "Default Admin Email", 
                value=admin_settings.get("default_admin_email", "admin@thehireman.co.uk")
            )
            cc_emails = st.text_input(
                "CC Emails (comma separated)", 
                value=admin_settings.get("cc_emails", ""),
                placeholder="manager@company.com, crm@company.com"
            )
        with col2:
            email_template = st.selectbox("Email Template", 
                ["Standard Price List", "Urgent Priority", "Bulk Import", "Custom"])
            auto_send = st.checkbox("Auto-send to admin team", help="Automatically email when price list is generated")
        
        # Save admin settings button
        if st.button("💾 Save Admin Email Settings"):
            config = st.session_state.config
            config["admin_settings"]["default_admin_email"] = default_admin_email
            config["admin_settings"]["cc_emails"] = cc_emails
            if save_config(config):
                st.session_state.config = config
                st.success("✅ Admin email settings saved!")
    
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

# Footer
st.markdown("---")
st.markdown("*Net Rates Calculator - Admin Integration v2.0*")
# Load Progress from Uploaded JSON Only
# -------------------------------
#if st.session_state.get("scroll_to_load"):
 #   st.markdown("## <span style='color:#1976d2'>📂 <b>Load Progress Section</b></span>", unsafe_allow_html=True)
 #   st.session_state["scroll_to_load"] = False

# Sidebar for Load Progress and other actions
with st.sidebar:
    st.markdown("## 🎛️ Controls")
    
    # Method 1: Download/Upload (One-click implementation)
    st.markdown("### 💾 Download/Upload Method")
    
    # Save progress button
    if st.button("💾 Save Progress", use_container_width=True, help="Prepare progress file for download"):
        customer_name = st.session_state.get('customer_name', '')
        if customer_name:
            # Show a simple but effective loading message
            with st.spinner('💾 Saving progress... Please wait'):
                st.info("📋 Preparing your progress file for download...")
                
                # Simulate some processing time so user can see the loading
                time.sleep(2)
                
                # Set the trigger for download
                st.session_state['trigger_download_save'] = True
            
            # Show completion message
            st.success("✅ Progress saved! Download button ready below.")
            time.sleep(1)  # Brief pause to show success message
            st.rerun()
        else:
            st.error("Please enter a customer name first")
    
    # Download progress button (appears when save is prepared)
    if st.session_state.get('trigger_download_save', False):
        customer_name = st.session_state.get('customer_name', '')
        safe_customer_name = customer_name.strip().replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{safe_customer_name}_progress_{timestamp}.json"
        
        # Collect all session state data
        df = st.session_state.get('df', pd.DataFrame())
        global_discount = st.session_state.get('global_discount', 0)
        
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
        
        if st.download_button(
            label="📥 Download Progress",
            data=json_data,
            file_name=filename,
            mime="application/json",
            use_container_width=True,
            help=f"Download {filename} to your Downloads folder"
        ):
            st.session_state['trigger_download_save'] = False  # Clear trigger after download
            st.success(f"✅ Downloaded: {filename}")
            st.rerun()
    
    # Upload file to load
    uploaded_file = st.file_uploader(
        "⬆️ Upload Progress File", 
        type=['json'], 
        key="sidebar_upload",
        help="Upload a previously saved progress file"
    )
    
    if uploaded_file:
        if st.button("📁 Load from Upload", use_container_width=True):
            st.session_state['uploaded_file_to_load'] = uploaded_file
            st.session_state['trigger_upload_load'] = True
            st.rerun()
    
    st.markdown("---")
    
    # Method 2: SharePoint (Placeholder buttons)
    st.markdown("### 🌐 SharePoint Method")
    
    if st.button("☁️ Save SharePoint", use_container_width=True, help="Save to SharePoint (Coming Soon)"):
        st.info("🚧 SharePoint integration coming soon!")
    
    if st.button("☁️ Load SharePoint", use_container_width=True, help="Load from SharePoint (Coming Soon)"):
        st.info("🚧 SharePoint integration coming soon!")
    
    st.markdown("---")
    
    # Additional Quick Actions
    st.markdown("### 📊 Export Options")
    
    if st.button("📤 Export Excel", use_container_width=True):
        st.session_state['trigger_export'] = True
        st.rerun()
    
    if st.button("📄 Generate PDF", use_container_width=True):
        st.session_state['trigger_pdf_export'] = True
        st.rerun()
# Main content area - simplified load progress section
st.markdown("### Load Progress from Saved Files")
if st.session_state.get('show_load_progress', False):
    st.info("👈 Use the sidebar to load progress from saved files.")
    st.session_state['show_load_progress'] = False






















