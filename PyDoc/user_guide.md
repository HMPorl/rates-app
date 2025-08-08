# Net Rates Calculator - User Guide

## Overview
The Net Rates Calculator is a web-based tool for generating customized equipment rental price lists with integrated email functionality.

## Quick Start Guide

### 1. Basic Setup
1. **Enter Customer Name** - Required for all exports and emails
2. **Upload Company Logo** (optional) - Will appear on PDF documents
3. **Select Sales Person PDF Header** - Choose your sales person template
4. **Show Admin Upload Options** (if needed) - For custom Excel files

### 2. Setting Discounts

#### Global Discount
- Set a base discount percentage that applies to all items
- Use the "Update all group discounts" button to apply globally

#### Group-Level Discounts
- Each equipment group can have its own discount percentage
- Override individual groups as needed
- Use "Set All Groups to Global Discount" to reset all groups

### 3. Custom Pricing

#### Automatic Pricing
- Items automatically show discounted prices based on your group settings
- Discount percentages are calculated and displayed

#### Manual Price Override
- Enter custom prices in the text boxes for specific items
- System shows if you exceed maximum allowed discount
- Only manually entered prices appear in the "Special Rates" section

### 4. Transport Charges
- Default values are pre-filled for common transport types
- Modify charges as needed for your customer
- These appear as a separate section in all exports

### 5. Export Options

#### Save Progress
- Download JSON file to save your current work
- Can be reloaded later to continue editing

#### Excel Export (Admin Format)
- Multi-sheet workbook with:
  - Price List: Complete equipment data
  - Transport Charges: Delivery options
  - Summary: Customer and creation details

#### CSV Export
- Universal format for other systems

#### JSON Export (API)
- Structured data for system integration

#### PDF Export
- Professional formatted price list
- Include/exclude special rates section
- Company logo and sales person header

### 6. Email Functionality

#### Email Configuration
- **SendGrid (Recommended)**: Best for reliable delivery and attachments
- **Gmail**: Requires app password setup
- **Office365**: Standard business email
- **Custom SMTP**: For other email providers

#### Sending Emails
- Emails include both Excel and JSON attachments
- Excel for CRM import
- JSON for calculator backup/reload
- CC yourself or others as needed
- Auto-generated professional email format

## Advanced Features

### Weather Display
- Toggle weather information on/off
- Shows current London weather and daily forecast

### Admin Options
- Upload custom Excel templates
- Upload custom PDF headers
- Override default files

### Progress Management
- Save work at any time with timestamps
- JSON files preserve all settings and custom prices
- Reload previous work to continue editing

## Troubleshooting

### Email Issues
- **SendGrid errors**: Check API key and from email address
- **Gmail issues**: Ensure 2-factor auth and app password are set up
- **Attachment problems**: SendGrid provides best attachment support

### Excel/PDF Export Issues
- Ensure customer name is entered
- Check file permissions if downloads fail
- PDF requires sales person header selection

### Performance Tips
- Use "Show Admin Upload Options" only when needed
- Save progress regularly for complex price lists
- Test email configuration before sending important quotes

## Best Practices

1. **Always enter customer name first** - Required for all exports
2. **Save progress frequently** - Especially for large price lists
3. **Test email settings** - Use the test button before sending quotes
4. **Use SendGrid for emails** - Most reliable for business use
5. **Review discount limits** - System warns when exceeding maximum discounts
6. **Keep PDF headers organized** - Name them clearly by sales person

## Support

For technical support or questions:
- Check this guide first
- Contact IT Support team
- Email: netrates@thehireman.co.uk

## Version Information
- Application: Net Rates Calculator
- Last Updated: August 2025
- Supported Browsers: Chrome, Firefox, Safari, Edge
