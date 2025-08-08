# GitHub Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a Python Streamlit application for generating equipment net rates price lists with integrated email functionality using SendGrid API.

## Key Components
- **Streamlit Web App**: Interactive pricing calculator interface
- **SendGrid Integration**: Professional email delivery with Excel attachments
- **PDF Generation**: ReportLab for professional price list documents
- **Excel Processing**: Multi-sheet workbooks with pandas and openpyxl
- **Configuration Management**: Persistent settings storage

## Architecture Guidelines
- Use modular design with separate files for email utilities, configuration, and main app logic
- Prioritize SendGrid for email delivery over webhook or SMTP alternatives
- Handle Excel files with multiple sheets: Price List, Transport Charges, Summary
- Maintain backward compatibility with existing configuration files
- Follow error handling best practices for external API integrations

## Code Style
- Use type hints for function parameters and return values
- Include comprehensive docstrings for all functions
- Handle exceptions gracefully with user-friendly error messages
- Use environment variables for sensitive configuration (API keys)
- Follow PEP 8 style guidelines

## Email Integration Priority
1. SendGrid API (recommended for best attachment support)
2. Webhook with SendGrid fallback
3. Traditional SMTP configurations
4. Manual email preparation as fallback

## Testing Considerations
- Test email configurations before sending
- Validate Excel file structure and required columns
- Handle missing PDF templates gracefully
- Provide clear user feedback for all operations
