# Configuration Setup

## Important Security Notice
⚠️ **Never commit your `config.json` file with real API keys to Git!**

The `config.json` file is automatically ignored by Git to protect your sensitive credentials.

## Initial Setup

1. **Copy the template file:**
   ```bash
   cp config.template.json config.json
   ```

2. **Add your credentials to `config.json`:**
   - Open `config.json` in a text editor
   - Add your SendGrid API key, email settings, etc.
   - Save the file

3. **Configure in the app:**
   - Run the Streamlit app
   - Go to "SMTP Configuration" section
   - Enter your credentials and click "💾 Save Settings"

## What Gets Saved

- **SendGrid**: API key and from email
- **Gmail**: Email address and app password
- **Office365**: Email and password
- **Custom SMTP**: Server details and credentials
- **Admin Settings**: Default admin emails

## File Security

- `config.json` - Contains your actual credentials (NOT synced to Git)
- `config.template.json` - Template file (safe to sync to Git)
- Both files are required for the app to work properly

## Backup Your Settings

To backup your configuration:
1. Copy your `config.json` file to a secure location
2. Do NOT commit it to Git or share it publicly

## Troubleshooting

If you see "GitHub Push Protection" errors:
- Make sure `config.json` is in your `.gitignore` file
- Remove any API keys from files being committed
- Use the template file for sharing code
