import os
import json
import streamlit as st
from config import OUTPUT_DIR
from store_data import display_results

def view_results():
    st.title("View Results")
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    if files:
        selected_file = st.selectbox("Select a file:", files)
        try:
            with open(os.path.join(OUTPUT_DIR, selected_file), "r") as f:
                data = json.load(f)
        
            df = display_results(data)
            st.dataframe(df)
        except Exception as e:
            st.write("An error occurred while reading the file.")
            st.error(e)
    else:
        st.write("No results available yet.")