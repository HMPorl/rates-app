"""
Streamlit launcher for Net Rates Calculator
This file provides a simple way to run either the enhanced or original app
"""

import streamlit as st
import os
import sys

# Add current directory to path
sys.path.append('.')

st.set_page_config(
    page_title="Net Rates Calculator",
    page_icon="💰",
    layout="wide"
)

# App Selection
st.title("💰 Net Rates Calculator")
st.markdown("**Professional Equipment Pricing with Email Integration**")

# Show both app options
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Enhanced App (Recommended)")
    st.markdown("""
    **Features:**
    - ✅ Optimized SendGrid integration
    - ✅ Improved email configuration UI
    - ✅ Better error handling
    - ✅ Modular architecture
    - ✅ Analytics dashboard
    """)
    
    if st.button("Launch Enhanced App", type="primary"):
        st.info("🔄 The enhanced app with modular design is being prepared...")
        st.markdown("**Note:** Use the original app below for immediate access to all features.")

with col2:
    st.subheader("📋 Original App (Full Featured)")
    st.markdown("""
    **Features:**
    - ✅ Complete pricing calculator
    - ✅ PDF generation with headers
    - ✅ Excel multi-sheet export
    - ✅ SendGrid email integration
    - ✅ Transport charges
    - ✅ Group discounting
    """)
    
    if st.button("Launch Original App", type="primary"):
        # Run the original app by redirecting
        st.markdown("**Redirecting to original app...**")
        st.markdown("Please run: `streamlit run app.py` in your terminal")

# Quick Start Guide
st.markdown("---")
st.subheader("🚀 Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **1. Setup Email**
    - Get SendGrid API key
    - Configure in app settings
    - Test email connection
    """)

with col2:
    st.markdown("""
    **2. Upload Files**
    - Excel rates file
    - PDF header template
    - Company logo (optional)
    """)

with col3:
    st.markdown("""
    **3. Generate Lists**
    - Set customer name
    - Configure discounts
    - Email to admin team
    """)

# Environment Check
st.markdown("---")
st.subheader("⚙️ Environment Status")

# Check for required files
files_status = {
    "app.py": os.path.exists("app.py"),
    "config.py": os.path.exists("config.py"),
    "email_utils.py": os.path.exists("email_utils.py"),
    "requirements.txt": os.path.exists("requirements.txt")
}

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Files:**")
    for file, exists in files_status.items():
        status = "✅" if exists else "❌"
        st.text(f"{status} {file}")

with col2:
    st.markdown("**Environment Variables:**")
    env_vars = {
        "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", "Not set"),
        "WEBHOOK_EMAIL_URL": os.getenv("WEBHOOK_EMAIL_URL", "Not set")
    }
    
    for var, value in env_vars.items():
        if value != "Not set":
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
            st.text(f"✅ {var}: {masked_value}")
        else:
            st.text(f"⚠️ {var}: {value}")

# Instructions
st.markdown("---")
st.subheader("📝 Next Steps")

if all(files_status.values()):
    st.success("✅ All files are present! Ready to launch the application.")
    st.markdown("""
    **To get started:**
    1. Run `streamlit run app.py` in your terminal for the full-featured app
    2. Or configure the enhanced modular version above
    3. Upload your Excel rates file and PDF header
    4. Configure SendGrid for best email experience
    """)
else:
    st.warning("⚠️ Some files are missing. Please ensure all required files are in the workspace.")

# Terminal Command Helper
st.markdown("---")
st.subheader("💻 Terminal Commands")

st.code("""
# Run the original full-featured app
streamlit run app.py

# Install missing dependencies
pip install -r requirements.txt

# Check Python environment
python --version

# Test SendGrid integration
python -c "from sendgrid import SendGridAPIClient; print('SendGrid available')"
""", language="bash")

st.markdown("---")
st.markdown("*Net Rates Calculator Workspace - Ready for Development*")
