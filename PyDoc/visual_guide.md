# Net Rates Calculator - Visual Step-by-Step Guide

## 📋 **Complete Walkthrough**

### Phase 1: Initial Setup
```
┌─────────────────────────────────────────────┐
│  Step 1: Enter Customer Name                │
│  [Customer Name Input Box]                  │
│  ⚠️  Required for all exports               │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Step 2: Upload Company Logo (Optional)     │
│  [Logo Upload Area]                         │
│  💡 Appears on PDF documents               │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Step 3: Select Sales Person PDF Header     │
│  [Dropdown: Select Sales Person]            │
│  ⚠️  Required for PDF generation            │
└─────────────────────────────────────────────┘
```

### Phase 2: Configure Pricing
```
┌─────────────────────────────────────────────┐
│  Step 4: Set Global Discount                │
│  [Global Discount %: ___]                   │
│  [🔄 Update all group discounts] ←── Click  │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Step 5: Adjust Group Discounts             │
│  [Group 1: ___% ] [Group 2: ___% ]         │
│  [Group 3: ___% ] [Group 4: ___% ]         │
│  💡 Can override individual groups          │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Step 6: Custom Prices (Optional)           │
│  Item Category | Equipment | Price | Custom │
│  Excavator     | 1.5T Mini | £150  | [___] │
│  💡 Only fill boxes for special pricing     │
└─────────────────────────────────────────────┘
```

### Phase 3: Transport & Export
```
┌─────────────────────────────────────────────┐
│  Step 7: Review Transport Charges           │
│  Standard tools: £5                         │
│  Towables: £7.5                            │
│  💡 Modify default values as needed         │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Step 8: Choose Export Method               │
│  [📊 Excel] [📄 PDF] [📨 Email] [💾 Save]  │
│                                             │
│  📊 Excel → For CRM import                  │
│  📄 PDF → Customer-facing quote             │
│  📨 Email → Send to accounts team           │
│  💾 Save → Backup your work                 │
└─────────────────────────────────────────────┘
```

### Phase 4: Email Setup (One-Time Configuration)
```
┌─────────────────────────────────────────────┐
│  Email Config Toggle: [OFF] → [ON]          │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Choose Email Provider:                     │
│  ○ Not Configured                           │
│  ● SendGrid (Recommended)                   │
│  ○ Gmail                                    │
│  ○ Outlook/Office365                        │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  SendGrid Configuration:                    │
│  API Key: [your_api_key_here]               │
│  From Email: [netrates@thehireman.co.uk]    │
│  [💾 Save SendGrid Settings]                │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Test Configuration:                        │
│  [🧪 Test Email Configuration]              │
│  ✅ Ready to send emails!                   │
└─────────────────────────────────────────────┘
```

## 🎯 **Decision Tree: Which Export Should I Use?**

```
START: I need to...
    │
    ├── Send to customer
    │   └── Use: 📄 Download as PDF
    │
    ├── Import to CRM system  
    │   └── Use: 📊 Download Excel (Admin Format)
    │
    ├── Continue work later
    │   └── Use: 💾 Save Progress
    │
    ├── Send to accounts team
    │   └── Use: 📨 Send Email to Admin Team
    │       │
    │       ├── Includes Excel file (for CRM)
    │       ├── Includes JSON backup file  
    │       └── CC myself: [optional email]
    │
    └── Export for other software
        └── Use: 📄 Download CSV
```

## ⚡ **Speed Tips**

### Keyboard Shortcuts
- **Tab** → Move between input fields
- **Enter** → Confirm number inputs
- **Ctrl+S** → Browser save (not app save)

### Mouse Workflows
1. **Quick Setup**: Name → Header → Global Discount → PDF
2. **Detailed Setup**: Name → Header → Group Discounts → Custom Prices → Email
3. **Save & Continue**: Regular Save Progress downloads

### Time-Saving Features
- "🔄 Update all group discounts" applies global to all groups
- "🔄 Set All Groups to Global Discount" resets everything
- Weather toggle (turn off to reduce load time)
- Email config stays saved between sessions

## 🚨 **Error Prevention Checklist**

Before clicking any export button:
- ✅ Customer name entered?
- ✅ PDF header selected? (for PDF export)
- ✅ Discount percentages reasonable?
- ✅ Email configuration tested? (for email sending)

## 📱 **Mobile/Tablet Usage**

The app works on mobile devices but desktop is recommended for:
- ✅ Better table viewing
- ✅ Easier multiple file downloads  
- ✅ More reliable email configuration
- ✅ Better PDF preview

Mobile is fine for:
- ✅ Quick price checks
- ✅ Viewing saved progress
- ✅ Simple discount adjustments

---
**🔄 Last Updated**: August 2025 | **📧 Support**: netrates@thehireman.co.uk
