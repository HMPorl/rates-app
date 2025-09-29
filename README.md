# Net Rates Calculator - README

## Project Overview

The Net Rates Calculator is a comprehensive Streamlit web application designed for The Hireman to generate professional price lists and quotes for equipment rental. The application allows users to apply discounts, set custom pricing, and export data in multiple formats with professional branding.

## Version History

### V2.0 (Current) - Enhanced Professional Calculator
- Complete rewrite with custom price management
- Transport charges integration across all exports
- UK timezone support and professional formatting
- Streamlined UI with visual indicators (🎯 for custom prices, 📊 for calculated)
- Performance optimizations for large datasets
- Removed weather functionality (archived in v1-archive branch)

### V1.0 (Archived in v1-archive branch)
- Basic pricing calculator functionality
- Original weather integration (removed in V2)
- Foundation export capabilities

## Architecture & Design Philosophy

### Core Design Principles
- **User-Centric Interface**: Streamlined workflow with visual indicators and intuitive controls
- **Data Integrity**: Robust handling of pricing data, POA values, and session state management
- **Professional Output**: Consistent formatting across all export formats (Excel, PDF, Email)
- **Performance Optimized**: Efficient handling of large datasets (100+ items) with progress indicators
- **Error Resilient**: Comprehensive error handling and graceful fallbacks

### Technical Stack
- **Framework**: Streamlit (web interface)
- **Data Processing**: Pandas (Excel/CSV handling)
- **PDF Generation**: ReportLab + PyMuPDF (professional layouts)
- **Email Services**: SendGrid API (primary), SMTP fallback
- **Session Management**: Streamlit session state with safe initialization
- **File Handling**: Multi-format support (Excel, CSV, JSON, PDF)
- **Timezone**: UK timezone (Europe/London) for all timestamps

## Application Logic Flow

### 1. Authentication & Security
```python
# PIN-based authentication system
if not st.session_state.authenticated:
    # Username: "HM", PIN: "1985"
    # Blocks access to main application features
```

### 2. Data Loading & Validation
```python
# Priority order for data loading:
# 1. Admin uploaded Excel file (via sidebar)
# 2. Default Excel file with timestamp-based cache invalidation
# 3. Graceful handling when no file exists

# Required columns validation:
required_columns = {"ItemCategory", "EquipmentName", "HireRateWeekly", 
                   "GroupName", "Sub Section", "Max Discount", "Include", "Order"}
```

### 3. Pricing Logic Architecture

#### Three-Tier Pricing System
1. **Global Discount**: Base percentage applied to all items
2. **Group-Level Discounts**: Customizable per equipment group/subsection
3. **Custom Prices**: Manual overrides with visual indicators

#### Custom Pricing States
```python
# Three pricing states per item:
# 1. Calculated (group discount applied) - 📊 indicator
# 2. Custom (manual override) - 🎯 indicator  
# 3. POA (Price on Application) - handles non-numeric values

def get_discounted_price(row):
    """Calculate price based on group discount or return POA"""
    key = f"{row['GroupName']}_{row['Sub Section']}_discount"
    discount = st.session_state.get(key, global_discount)
    
def calculate_discount_percent(original, custom):
    """Calculate actual discount percentage, handling POA values"""
```

#### POA (Price on Application) Handling
```python
def is_poa_value(value):
    """Comprehensive POA detection for business flexibility"""
    return str(value).upper().strip() in ['POA', 'PRICE ON APPLICATION', 'CONTACT FOR PRICE']
```

### 4. Session State Management (Critical V2 Enhancement)

#### Safe Initialization Pattern
```python
# Critical: Initialize session state BEFORE widget creation
# Prevents StreamlitAPIException conflicts

def initialize_session_state():
    """Centralized session state setup with safe defaults"""
    
# Pattern used throughout:
if 'key_name' not in st.session_state:
    st.session_state['key_name'] = default_value
```

#### Progress Loading System
```python
def handle_file_loading():
    """Load saved progress BEFORE widgets are created"""
    # Uses trigger-based system to avoid rerun loops
    # Maps saved ItemCategory to current DataFrame indices
    # Handles large datasets efficiently with O(1) lookup
    # Includes progress indicators for 20+ items
```

### 5. Visual Indicators & UX (V2 Key Feature)

#### Emoji-Based Visual System
- **🎯 Custom Price**: User-entered specific pricing (appears in headers and items)
- **📊 Calculated Price**: Automatic group discount application
- **💡 Helpful Tips**: Guidance text throughout interface
- **⚠️ Max Discount Warning**: Prevents excessive discounting

#### Dynamic Header Indicators
```python
# Group headers show 🎯 if ANY item in group has custom pricing
has_custom_in_group = any(
    st.session_state.get(f"price_{idx}", "").strip() 
    for idx in group_df.index
)
header_text = f"{group} - {subsection}"
if has_custom_in_group:
    header_text += " 🎯"
```

### 6. Export System Architecture

#### Transport Charges Integration (V2 Critical Fix)
```python
# Fixed 8-category transport system (was 4, caused export errors):
transport_types = [
    "Road transport - 26 tonne lorry",
    "Road transport - 44 tonne lorry", 
    "Sea/Road transport",
    "Road transport - Transit van",
    "Air transport",
    "Rail transport",
    "Road transport - 7.5 tonne lorry",
    "Own arrangements"
]

# NOW INTEGRATED INTO ALL EXPORT FORMATS:
# - Excel (dedicated sheet with proper formatting)
# - PDF (embedded table on page 3)
# - Email attachments (both Excel and PDF)
# - CSV exports (when applicable)
```

#### Standardized Formatting Functions
```python
def format_price_for_export(value):
    """Numeric export format - handles POA, returns clean numbers"""
    
def format_price_display(value):
    """Display format with £ symbol for UI"""
    
def format_custom_price_for_export(value):
    """Custom price export with POA handling"""
    
def format_discount_for_export(value):
    """Discount percentage with % symbol"""
```

### 7. Email Integration

#### SendGrid API (Primary System)
```python
def send_email_via_sendgrid_api():
    """Professional email delivery with perfect attachment handling"""
    # Features:
    # - Dual attachments: Excel (for CRM) + JSON (for backup)
    # - Professional HTML formatting
    # - Base64 encoding for reliable attachment delivery
    # - UK timezone timestamps in content
    # - Custom email templates with branding
```

### 8. PDF Generation System

#### Advanced Two-Stage Layout Engine
```python
# Stage 1: ReportLab content generation
# - Price lists with alternating row colors
# - Professional typography and spacing
# - Transport charges table integration
# - Custom price highlighting (🎯 indicators)

# Stage 2: PyMuPDF header merging
# - Salesperson-specific headers
# - Customer name and logo insertion
# - Professional color schemes (#7DA6D8, #F7FCFF, #DAE9F8)
# - Transport table positioning and formatting
```

## Key Features & Functionality

### Bulk Operations (Simplified in V2)
- **Set All Groups to Global**: Sync all group discounts to global percentage
- **Clear All Custom Prices**: Reset all items to calculated pricing
- **Dynamic count displays**: All buttons show affected item counts
- **Removed**: Problematic "Apply Global to Non-Custom" (caused session state conflicts)

### Progress Management
- **One-Click Save**: Download JSON progress file with metadata
- **Smart Loading**: Maps saved prices to current data structure
- **Large Dataset Support**: Progress indicators for datasets with 20+ items
- **Customer Name Integration**: Progress files include customer context

### Professional Export Features
- **Admin Excel**: CRM-ready format with all metadata and calculations
- **Customer PDF**: Branded quotes with professional headers and transport info
- **Email Integration**: Dual attachments (Excel for import + JSON for backup)
- **UK Timezone**: All timestamps in Europe/London timezone

## Performance Optimizations (V2 Enhancements)

### Large Dataset Handling
```python
# Efficient groupby operations (calculated once, reused)
grouped_df = df.groupby(["GroupName", "Sub Section"])
group_keys = list(grouped_df.groups.keys())

# Progress indicators for operations affecting 20+ items
if len(items_to_process) >= 20:
    show_progress_bar()
```

### Session State Efficiency
```python
# Bulk operations processed before widget creation (prevents conflicts)
if st.session_state.get('bulk_operation_trigger', False):
    process_bulk_operation()  # Process before any st.text_input() calls
```

## Development Journey & Lessons Learned

### V1 to V2 Migration Challenges Solved
1. **Transport Charges Missing**: Arrays mismatch (4 vs 8 categories) fixed
2. **Session State Conflicts**: StreamlitAPIException resolved with safe initialization
3. **Custom Price Overwrites**: Simplified bulk operations to avoid conflicts
4. **Export Inconsistencies**: Standardized formatting across all export methods
5. **Performance Issues**: Optimized groupby operations and progress loading

### Critical Code Patterns
```python
# Safe session state pattern (prevents widget conflicts)
if st.session_state.get('trigger_flag', False):
    st.session_state['trigger_flag'] = False
    # Process bulk operation BEFORE creating widgets
    
# Visual feedback pattern
st.success("✅ Operation completed successfully")
st.info("💡 Helpful tip: Enter 'POA' for special rates")
```

### Architecture Decisions
- **Removed weather functionality**: Simplified focus on core business needs
- **Emoji indicators**: Improved UX without technical complexity
- **Transport integration**: Fixed critical business requirement
- **UK timezone**: Professional consistency across all outputs

## Future Development Notes

### Potential Enhancements
- **Multi-currency Support**: Extend beyond GBP
- **Role-based Access**: Different permissions for different users
- **Advanced Reporting**: Analytics dashboard for pricing patterns
- **API Integration**: Direct CRM system integration

### Known Dependencies
```python
# Core requirements
streamlit>=1.28.0
pandas>=1.5.0
openpyxl>=3.1.0
reportlab>=4.0.0
PyMuPDF>=1.23.0
sendgrid>=6.10.0
pytz>=2023.3  # For UK timezone support
```

## Business Logic Summary

This application serves The Hireman's core business need for professional, accurate, and efficient price list generation. The V2 enhancement focuses on:

1. **Professional Output**: All exports (Excel, PDF, email) maintain brand standards
2. **User Efficiency**: Visual indicators and streamlined workflows reduce errors
3. **Data Accuracy**: Transport charges included, UK timezone consistency
4. **Business Flexibility**: POA handling, custom pricing, group discounts
5. **Technical Reliability**: Robust error handling, session state management

---

**For AI Context Restoration**: This README provides comprehensive context for resuming development. The application is production-ready V2 with archived V1 backup. Key solved issues: transport charges integration, custom pricing with visual indicators, session state conflicts resolved, and professional export consistency achieved.