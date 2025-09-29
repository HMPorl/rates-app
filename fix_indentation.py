#!/usr/bin/env python3
"""
Quick script to fix the indentation issue in the Load Progress section
"""

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic lines
for i, line in enumerate(lines):
    # Look for the specific problem lines around line 2652-2656
    if i >= 2650 and i <= 2660:
        if line.strip().startswith('# Create tabs for different load options'):
            lines[i] = '    # Create tabs for different load options\n'
        elif 'tab1, tab2, tab3 = st.tabs' in line and not line.startswith('    '):
            lines[i] = '    tab1, tab2, tab3 = st.tabs(["📁 Local Files", "☁️ Google Drive Files", "📤 Upload File"])\n'
        elif line.strip() == 'with tab1:' and not line.startswith('    '):
            lines[i] = '    with tab1:\n'

# Write back to file
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed indentation issues in app.py")