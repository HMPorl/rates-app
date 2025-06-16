# 1. Import Streamlit
import streamlit as st

# 2. Set the title of the app
st.title("Net Rates Calculator")

# 3. Add a description or instructions
st.write("Upload your pricing spreadsheet to calculate net rates.")

# 4. File uploader
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

# 5. Process the uploaded file
if uploaded_file is not None:
    import pandas as pd

    # Read the file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Display the uploaded data
    st.subheader("Uploaded Data")
    st.dataframe(df)

    # Example calculation: Add a 'Net Rate' column
    if 'Price' in df.columns:
        df['Net Rate'] = df['Price'] * 0.9  # Example 10% discount
        st.subheader("With Net Rates")
        st.dataframe(df)
    else:
        st.warning("No 'Price' column found in the uploaded file.")
