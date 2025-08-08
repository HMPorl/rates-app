# Net Rates Calculator

A professional Streamlit web application for generating equipment rental price lists with integrated email functionality using SendGrid API.

## 🚀 Features

- **Interactive Pricing Calculator**: Web-based interface for creating custom equipment price lists
- **SendGrid Email Integration**: Professional email delivery with perfect Excel attachments  
- **Multi-Sheet Excel Export**: Price List, Transport Charges, and Summary sheets
- **PDF Generation**: Professional branded price list documents
- **Flexible Configuration**: Support for multiple email providers and settings
- **Group Discounting**: Bulk discount management by equipment categories
- **Transport Charges**: Customizable delivery and collection pricing

## 📋 Requirements

- Python 3.8+
- Streamlit
- SendGrid account (recommended for email functionality)
- Excel files with equipment data

## 🛠️ Installation

1. **Clone or download this repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your SendGrid API key and other settings
   ```

4. **Run the application:**
   ```bash
   streamlit run main.py
   ```

## ⚙️ Configuration

### Email Setup (Choose one):

#### Option 1: SendGrid API (Recommended)
- Best for reliable Excel attachments
- Sign up at [SendGrid.com](https://sendgrid.com)
- Get API key from Settings → API Keys
- Configure in the app's Email Configuration panel

#### Option 2: Webhook Integration
- Set `WEBHOOK_EMAIL_URL` environment variable
- Works with Zapier or similar webhook services

#### Option 3: Traditional SMTP
- Gmail, Outlook, or custom SMTP servers
- Configure through the app interface

### Required Files

1. **Excel Rate File**: Must contain columns:
   - ItemCategory, EquipmentName, HireRateWeekly
   - GroupName, Sub Section, Max Discount
   - Include, Order

2. **PDF Header Template**: Optional branded header for price lists

## 🎯 Usage

1. **Start the app**: `streamlit run main.py`
2. **Enter customer information**
3. **Upload Excel rate file**
4. **Configure group discounts**
5. **Adjust individual prices if needed**
6. **Generate and email price list**

## 📊 Email Functionality

The app prioritizes email methods in this order:
1. **SendGrid API** (best attachment support)
2. **Webhook with SendGrid fallback**
3. **Configured SMTP provider**
4. **Manual email preparation**

## 🏗️ Project Structure

```
├── main.py              # Enhanced Streamlit app with SendGrid
├── app.py               # Original full-featured app
├── config.py            # Configuration management
├── email_utils.py       # Email and attachment utilities
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── .github/
    └── copilot-instructions.md
```

## 🔧 Development

### Key Components

- **config.py**: Handles persistent configuration storage
- **email_utils.py**: SendGrid integration and Excel attachment creation
- **main.py**: Enhanced Streamlit interface with better email integration

### Adding Features

1. Email providers: Extend `email_utils.py`
2. Excel formats: Modify `create_excel_attachment()`
3. PDF customization: Update PDF generation functions
4. UI improvements: Enhance `main.py` interface

## 🐛 Troubleshooting

### Email Issues
- **No emails received**: Check SendGrid API key and verified sender
- **Attachment problems**: Use SendGrid instead of webhook/SMTP
- **Configuration errors**: Verify settings in Email Configuration panel

### File Issues
- **Excel errors**: Ensure all required columns are present
- **PDF problems**: Check PDF header template file exists

### Performance
- Large Excel files may take time to process
- Email delivery depends on provider (SendGrid is fastest)

## 📝 Environment Variables

```bash
# SendGrid (recommended)
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=youremail@domain.com

# Webhook (alternative)
WEBHOOK_EMAIL_URL=https://hooks.zapier.com/hooks/catch/...

# Application
DEFAULT_ADMIN_EMAIL=admin@yourcompany.com
DEBUG_MODE=False
```

## 🚀 Deployment

### Local Development
```bash
streamlit run main.py
```

### Production Deployment
1. Set environment variables
2. Configure SendGrid API key
3. Deploy to your preferred platform (Streamlit Cloud, Heroku, etc.)

## 📞 Support

For issues with:
- **SendGrid integration**: Check API key and verified sender
- **Excel formatting**: Verify column names and data types
- **PDF generation**: Ensure header template is valid
- **General questions**: Review the configuration panel help text

## 🔄 Updates

This workspace includes both the enhanced `main.py` (recommended) and original `app.py` for compatibility. Use `main.py` for the best SendGrid integration experience.
