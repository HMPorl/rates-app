# Net Rates Calculator - Secure Setup Guide

## Security Configuration

This application uses environment variables to store sensitive information like API keys. **Never commit API keys or passwords to version control.**

## Setup Instructions

### 1. Environment Variables Setup

The application requires the following environment variables:

```bash
SENDGRID_API_KEY=your_sendgrid_api_key_here
SENDGRID_FROM_EMAIL=your_verified_sender_email@yourdomain.com
```

### 2. Setting Environment Variables

#### Windows (PowerShell) - Temporary (current session only):
```powershell
$env:SENDGRID_API_KEY="your_actual_api_key_here"
$env:SENDGRID_FROM_EMAIL="netrates@thehireman.co.uk"
```

#### Windows (Command Prompt) - Temporary:
```cmd
set SENDGRID_API_KEY=your_actual_api_key_here
set SENDGRID_FROM_EMAIL=netrates@thehireman.co.uk
```

#### Windows - Permanent (System Environment Variables):
1. Open System Properties → Advanced → Environment Variables
2. Add new system variables:
   - `SENDGRID_API_KEY` = your actual SendGrid API key
   - `SENDGRID_FROM_EMAIL` = your verified sender email

#### Linux/Mac - Temporary:
```bash
export SENDGRID_API_KEY="your_actual_api_key_here"
export SENDGRID_FROM_EMAIL="netrates@thehireman.co.uk"
```

#### Linux/Mac - Permanent:
Add to your `.bashrc` or `.zshrc`:
```bash
export SENDGRID_API_KEY="your_actual_api_key_here"
export SENDGRID_FROM_EMAIL="netrates@thehireman.co.uk"
```

### 3. Alternative: Use .env File (Optional)

You can also create a `.env` file in the project root:

1. Copy `.env.example` to `.env`
2. Fill in your actual values
3. Install python-dotenv: `pip install python-dotenv`
4. Add this to the top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

**Important:** The `.env` file is already in `.gitignore` to prevent accidental commits.

## SendGrid Setup

1. Sign up for SendGrid account
2. Verify your sender email address
3. Create an API key with "Mail Send" permissions
4. Use the API key and verified email in your environment variables

## Security Best Practices

✅ **DO:**
- Use environment variables for API keys
- Keep `.env` files local (never commit)
- Use different API keys for development/production
- Regularly rotate API keys
- Verify sender domains in SendGrid

❌ **DON'T:**
- Put API keys directly in code
- Commit `.env` files or `config.json` with secrets
- Share API keys in chat/email
- Use production keys in development

## Running the Application

```bash
streamlit run app.py
```

The app will automatically detect if environment variables are set and show the appropriate configuration status.
