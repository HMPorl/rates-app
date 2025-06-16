import os
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
import pandas as pd
from io import BytesIO

# SharePoint site and file details
sharepoint_url = "https://hireman.sharepoint.com/sites/BusinessSupport"
relative_url = "/sites/BusinessSupport/Shared Documents/Net Rates Master.xlsx"

# Use environment variables for credentials
username = os.getenv("SP_USERNAME")
password = os.getenv("SP_PASSWORD")

if not username or not password:
    print("❌ Environment variables SP_USERNAME or SP_PASSWORD are not set.")
    print("Please set them in your terminal before running this script.")
    exit()

# Authenticate and download the Excel file
ctx_auth = AuthenticationContext(sharepoint_url)
if ctx_auth.acquire_token_for_user(username, password):
    ctx = ClientContext(sharepoint_url, ctx_auth)

    # Create a BytesIO object to hold the file content
    file_obj = BytesIO()
    file = ctx.web.get_file_by_server_relative_url(relative_url)
    file.download(file_obj).execute_query()  # ✅ This is the correct usage

    # Move to the beginning of the file before reading
    file_obj.seek(0)

    # Load the Excel file into a pandas DataFrame
    df = pd.read_excel(file_obj, engine='openpyxl')

    print("✅ Excel file loaded successfully!")
    print(df.head())
else:
    print("❌ Authentication failed. Please check your credentials.")

