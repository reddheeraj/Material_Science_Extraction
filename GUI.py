import os
import streamlit as st
from config import PAPER_DIR, OUTPUT_DIR
from ui_functions.upload_n_process import upload_n_process
from ui_functions.query_results import query_results
from ui_functions.view_results import view_results

# Streamlit app configuration
st.set_page_config(page_title="Research Paper Processor", page_icon="🔄", layout="wide")

# Ensure directories exist
if not os.path.exists(PAPER_DIR):
    os.makedirs(PAPER_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Upload & Process", "Query Results", "View Results"])

menu_dict = {
    "Upload & Process": upload_n_process,
    "Query Results": query_results,
    "View Results": view_results
}

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Developed by Tau Group - Dheeraj**")  
                
def main():
    if menu:
        menu_dict[menu]()

if __name__ == "__main__":
    main()