import os
import streamlit as st
from config import PAPER_DIR, OUTPUT_DIR
from ui_functions.upload_n_process import upload_n_process
from ui_functions.query_results import query_results
from ui_functions.view_results import view_results
from ui_functions.dashboard import dashboard
from streamlit_option_menu import option_menu

# Streamlit app configuration
st.set_page_config(page_title="Material Science Data RAG", page_icon="🔄", layout="wide")

# Ensure directories exist
if not os.path.exists(PAPER_DIR):
    os.makedirs(PAPER_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# st.sidebar.title("Navigation")
with st.sidebar:
    menu = option_menu("Navigation", 
        ["View Results", "Upload & Process", "Query Results", "Analytics Dashboard"],
        icons=['house', 'cloud-upload', "list-task", 'gear'],
        styles={
            "container": {"padding": "2px", "background-color": "#00000"},
            "icon": {"color": "white", "font-size": "16px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#010101"},
            "nav-link-selected": {"background-color": "orange"},
        }               
    )

menu_dict = {
    "Upload & Process": upload_n_process,
    "Query Results": query_results,
    "View Results": view_results,
    "Analytics Dashboard": dashboard
}

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Developed by Tau Group - Dheeraj**")  
                
def main():
    if menu:
        menu_dict[menu]()

if __name__ == "__main__":
    main()