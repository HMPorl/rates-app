# Net Rates Calculator - Troubleshooting FAQ

## 🔧 **Common Issues & Solutions**

### 📧 **Email Problems**

#### "SendGrid API error: 'ItemCategory' error"
**Solution**: This is fixed in the latest version. If you see this:
1. Refresh the page
2. Re-enter your data
3. Contact support if it persists

#### "SendGrid API key not configured"
**Solution**: 
1. Click "Email Config" toggle
2. Select "SendGrid"
3. Enter your API key and from email
4. Click "💾 Save SendGrid Settings"

#### "Gmail authentication failed"
**Solution**:
1. Enable 2-Factor Authentication on Google account
2. Generate App Password: Google Account → Security → App passwords
3. Use the 16-character app password (not your regular password)

#### Email sent but recipient didn't receive it
**Solution**:
1. Check spam/junk folders
2. Verify email address spelling
3. Use SendGrid instead of other providers
4. Test with "🧪 Test Email Configuration"

### 📄 **PDF Export Issues**

#### "Cannot generate PDF"
**Solution**:
1. ✅ Enter customer name first
2. ✅ Select sales person PDF header
3. ✅ Refresh page if problem persists

#### PDF missing logo
**Solution**:
1. Upload logo in PNG, JPG, or JPEG format
2. Keep file size under 5MB
3. Logo appears on subsequent pages

#### PDF looks wrong/corrupted
**Solution**:
1. Try different browser (Chrome recommended)
2. Clear browser cache
3. Refresh page and regenerate

### 📊 **Excel Export Issues**

#### Excel file won't download
**Solution**:
1. Check browser download permissions
2. Ensure customer name is entered
3. Try different browser
4. Clear browser cache

#### Excel file appears corrupted
**Solution**:
1. Use latest version of Excel or LibreOffice
2. Try CSV export as alternative
3. Check file wasn't truncated during download

### 💾 **Save/Load Progress Issues**

#### Save Progress button doesn't work
**Solution**:
1. Enter customer name first
2. Check browser allows downloads
3. Try CSV export to test download functionality

#### Can't load previous progress
**Solution**:
Currently, the app doesn't have a built-in load feature. To restore progress:
1. Manually re-enter your previous settings
2. Use the JSON file as reference
3. Future versions will include load functionality

### 💰 **Pricing Calculation Issues**

#### Discounts not calculating correctly
**Solution**:
1. Check global discount is set correctly
2. Use "🔄 Update all group discounts" to sync
3. Refresh page if percentages look wrong

#### "Exceeds Max Discount" warnings
**This is normal** - the system warns when you go over limits:
1. Check if the discount is intentional
2. Reduce the discount percentage if needed
3. Override warnings are allowed for special cases

#### Custom prices not showing in final list
**This is normal** - custom prices only show in:
1. "Manually Entered Custom Prices" section
2. PDF export "Special Rates" section
3. All export files include both standard and custom pricing

### 🌐 **Browser Compatibility**

#### App looks broken or features missing
**Recommended browsers**:
- ✅ Chrome (best compatibility)
- ✅ Firefox
- ✅ Safari
- ✅ Microsoft Edge
- ❌ Internet Explorer (not supported)

#### Slow performance
**Solutions**:
1. Close other browser tabs
2. Turn off weather display
3. Use desktop instead of mobile for complex quotes
4. Clear browser cache

### 📱 **Mobile/Tablet Issues**

#### Hard to use on mobile
**This is expected** - the app is optimized for desktop:
1. Use landscape orientation
2. Zoom in on specific sections
3. Consider using desktop for complex quotes
4. Mobile works best for simple quotes

### 🔐 **Data Security Concerns**

#### Is my data saved on the server?
**No** - the app runs entirely in your browser:
1. No data is stored on servers
2. Save Progress downloads files to your device
3. Close browser tab = data is lost (unless saved)

#### Can I use this offline?
**No** - requires internet connection for:
1. App loading
2. Email sending
3. Weather information
4. But once loaded, pricing calculations work offline

## 🆘 **When All Else Fails**

### Emergency Procedures

#### Complete app failure
1. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)
2. **Clear browser cache** and reload
3. **Try different browser**
4. **Download Excel manually** and email it yourself

#### Lost work recovery
1. Check browser Downloads folder for any Save Progress files
2. Manually recreate using previous email attachments as reference
3. Contact support with details of when/what you were working on

#### Urgent quote needed
**Backup workflow**:
1. Use default discounts from global percentage
2. Download Excel immediately
3. Manually edit Excel file if needed
4. Email Excel file directly from your email client

## 📞 **Getting Support**

### Before contacting support:
1. ✅ Try refreshing the page
2. ✅ Check this FAQ
3. ✅ Try different browser
4. ✅ Note exactly what you were doing when error occurred

### When contacting support include:
- **Browser & version** (Chrome 91, Firefox 89, etc.)
- **Operating system** (Windows 10, macOS, etc.)
- **Exact error message** (screenshot if possible)
- **What you were trying to do**
- **Customer name and timestamp** (helps locate the issue)

### Support contacts:
- **📧 Email**: netrates@thehireman.co.uk
- **💬 Response time**: Usually within 1 business day
- **🚨 Urgent issues**: Mark email as "URGENT - Net Rates Calculator"

## 🔄 **App Updates**

### How to get latest version:
1. **Refresh browser page** (Ctrl+F5)
2. **Clear cache** if problems persist
3. **No installation needed** - updates automatically

### Recent fixes:
- ✅ SendGrid 'ItemCategory' error resolved
- ✅ Email attachment reliability improved
- ✅ PDF generation stability enhanced
- ✅ Transport charges default values added

---
**🕒 Last Updated**: August 2025 | **📧 Support**: netrates@thehireman.co.uk
