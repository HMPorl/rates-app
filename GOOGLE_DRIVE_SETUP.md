# Google Drive Integration Setup Guide

## Step 1: Get Your Service Account JSON File
1. From the Google Cloud Console credentials step, you should have downloaded a JSON file
2. Open this JSON file in a text editor
3. It will look something like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## Step 2: Add to Streamlit Cloud Secrets

### For Streamlit Cloud Deployment:
1. Go to your Streamlit Cloud app dashboard
2. Click on your app
3. Go to Settings → Secrets
4. Add this configuration (replace with your actual values):

```toml
[sendgrid]
SENDGRID_API_KEY = "your_sendgrid_api_key"
SENDGRID_FROM_EMAIL = "netrates@thehireman.co.uk"

[google_drive]
type = "service_account"
project_id = "your-actual-project-id"
private_key_id = "your-actual-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nyour-actual-private-key\n-----END PRIVATE KEY-----\n"
client_email = "your-actual-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-actual-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-actual-cert-url"
```

### For Local Development:
1. Create a `.streamlit` folder in your project directory
2. Create a file called `secrets.toml` inside the `.streamlit` folder
3. Copy the same configuration as above

## Step 3: Test the Integration

1. Deploy your updated code to Streamlit Cloud
2. Go to your app
3. Try the "Save Progress" button - it should save to Google Drive
4. Check the "Load Progress" section - it should list files from Google Drive

## Security Notes:
- Never commit the secrets.toml file to git
- The .streamlit folder is already in .gitignore
- Your service account only has access to the "Net Rates App" folder
- You can revoke access anytime by deleting the service account

## Troubleshooting:
- If you get "credentials not found" error, check the secrets formatting
- Make sure all JSON values are properly quoted in the TOML format
- Verify the service account email has been shared with the Google Drive folder
- Check the Streamlit Cloud logs for specific error messages

## Folder Structure Created:
```
Google Drive (staff.hireman@gmail.com)
└── Net Rates App/
    ├── Current_Saves/          (new progress files go here)
    └── Archive/                (move old files here manually)
```