# SMTP Email Configuration Guide
## Setting up Email Delivery for Net Rates Calculator

---

## 🚀 **Option 1: SendGrid (Recommended)**

SendGrid is ideal for business applications and offers reliable delivery with good reporting.

### **Setup Steps:**

1. **Get SendGrid Account:**
   - Visit [SendGrid](https://sendgrid.com/)
   - Sign up for free account (100 emails/day) or paid plan
   - Verify your account

2. **Create API Key:**
   - Log into SendGrid Console
   - Go to **Settings** → **API Keys**
   - Click **Create API Key**
   - Choose **Restricted Access**
   - Grant **Mail Send** permissions
   - Copy the generated API key (starts with `SG.`)

3. **Configure in App:**
   - Open your Net Rates Calculator
   - Expand "⚙️ SMTP Configuration"
   - Select "SendGrid"
   - Paste your API key
   - Set from email (e.g., `noreply@thehireman.com`)
   - Click "Test Email Configuration"

### **SendGrid Advantages:**
- ✅ 100 free emails per day
- ✅ High deliverability rates
- ✅ Detailed analytics and reporting
- ✅ Professional business solution
- ✅ Easy API integration

---

## 📧 **Option 2: Gmail (Simple Setup)**

Good for testing or small-scale use.

### **Setup Steps:**

1. **Enable 2-Factor Authentication:**
   - Go to Google Account settings
   - Security → 2-Step Verification
   - Enable it

2. **Generate App Password:**
   - In Google Account → Security
   - Click **App passwords**
   - Select **Mail** and **Other (Custom name)**
   - Copy the 16-character password

3. **Configure in App:**
   - Select "Gmail" in SMTP config
   - Enter your Gmail address
   - Enter the app password (not your regular password)

### **Gmail Limitations:**
- ⚠️ Daily sending limits (500 emails/day)
- ⚠️ May be flagged as personal email
- ⚠️ Less reliable for business use

---

## 🏢 **Option 3: Office365/Outlook**

If your company uses Microsoft 365.

### **Setup Steps:**

1. **Use Company Email:**
   - Enter your work email address
   - Enter your regular password

2. **Configure in App:**
   - Select "Outlook/Office365"
   - Enter credentials

### **Office365 Benefits:**
- ✅ Integrated with company email
- ✅ Professional appearance
- ✅ Good deliverability

---

## ⚙️ **Option 4: Custom SMTP**

For other email providers or company mail servers.

### **Common Settings:**

| Provider | SMTP Server | Port | TLS |
|----------|-------------|------|-----|
| **Yahoo** | smtp.mail.yahoo.com | 587 | Yes |
| **AOL** | smtp.aol.com | 587 | Yes |
| **Zoho** | smtp.zoho.com | 587 | Yes |
| **Company Server** | mail.yourcompany.com | 587/25 | Usually |

---

## 🔧 **Environment Variables (Secure Method)**

For production use, store credentials securely:

### **1. Create `.env` file:**
```
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
FROM_EMAIL=noreply@thehireman.com
ADMIN_EMAIL=admin@thehireman.com
```

### **2. Install python-dotenv:**
```bash
pip install python-dotenv
```

### **3. Load in your app:**
```python
from dotenv import load_dotenv
import os

load_dotenv()

smtp_config = {
    'enabled': True,
    'smtp_server': 'smtp.sendgrid.net',
    'smtp_port': 587,
    'username': 'apikey',
    'password': os.getenv('SENDGRID_API_KEY'),
    'from_email': os.getenv('FROM_EMAIL'),
    'use_tls': True
}
```

---

## 🛡️ **Security Best Practices**

### **For SendGrid:**
- ✅ Use restricted API keys (only Mail Send permission)
- ✅ Rotate API keys regularly
- ✅ Never commit keys to version control
- ✅ Use environment variables

### **For Gmail/Office365:**
- ✅ Use app passwords, not account passwords
- ✅ Enable 2-factor authentication
- ✅ Monitor for suspicious activity

### **General:**
- ✅ Use HTTPS in production
- ✅ Store credentials securely
- ✅ Log email activity for audit
- ✅ Validate recipient addresses

---

## 🚦 **Testing & Troubleshooting**

### **Common Issues:**

1. **"Authentication Failed"**
   - Check username/password
   - Verify API key permissions (SendGrid)
   - Ensure app password is used (Gmail)

2. **"Connection Timeout"**
   - Check firewall settings
   - Verify SMTP server and port
   - Try different port (25, 465, 587)

3. **"Emails Not Delivered"**
   - Check spam folder
   - Verify recipient email address
   - Check SendGrid activity dashboard

### **Test Steps:**
1. Configure SMTP in the app
2. Click "Test Email Configuration"
3. Send a test email to yourself
4. Check delivery and spam folders

---

## 📊 **Monitoring & Analytics**

### **SendGrid Dashboard:**
- View sent emails
- Check delivery rates
- Monitor bounces and spam reports
- Track open rates (if enabled)

### **App Logging:**
Consider adding logging to track email usage:
```python
import logging

logging.info(f"Email sent to {recipient} for customer {customer_name}")
```

---

## 🎯 **Recommended Setup for Your Company**

Based on your existing SendGrid usage:

1. **Use SendGrid** (you're already set up!)
2. **Create dedicated API key** for the rates calculator
3. **Set from email** as `noreply@thehireman.com`
4. **Add admin email** as `admin@thehireman.com`
5. **Test thoroughly** before going live

### **Quick Start Command:**
If you're already using SendGrid elsewhere, you likely have everything you need. Just:
1. Create a new API key in SendGrid console
2. Add it to the app configuration
3. Test and go live!

---

## 💡 **Advanced Features (Future)**

- **Email Templates:** Custom HTML templates
- **Bulk Email:** Send to multiple admins
- **Email Scheduling:** Send reports at specific times
- **Email Tracking:** Track opens and clicks
- **Attachment Optimization:** Compress large files

---

*Contact your IT team if you need help with company-specific email configurations.*
