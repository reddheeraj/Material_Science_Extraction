import streamlit as st

import os
import click
import shutil
import streamlit as st
from datetime import datetime
from index_files import main_function
from query_db import process_query
from config import PAPER_DIR, OUTPUT_DIR, BATCH_SIZE
from logger import logger

# Streamlit app configuration
st.set_page_config(page_title="Research Paper Processor", page_icon="🔄", layout="wide")

# Ensure directories exist
if not os.path.exists(PAPER_DIR):
    os.makedirs(PAPER_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Sidebar
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Upload & Process", "Query Results"])

# File Upload and Processing
if menu == "Upload & Process":
    st.title("Upload Research Papers for Processing")
    st.write("Upload your PDF files, and the system will process them to index the content for semantic search.")

    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(PAPER_DIR, file.name)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
        st.success(f"Uploaded {len(uploaded_files)} file(s) successfully.")

    if st.button("Process Files"):
        with st.spinner("Indexing papers into the database. This might take a while..."):
            main_function(PAPER_DIR, BATCH_SIZE)
        st.success("Processing completed! Your papers are now indexed for querying.")

# Query Results
if menu == "Query Results":
    st.title("Query Indexed Papers")
    st.write("Search through the indexed content by entering a query.")

    query = st.text_input("Enter your query:", "")
    if st.button("Search"):
        if not query.strip():
            st.warning("Please enter a query before searching.")
        else:
            with st.spinner("Querying the database and refining results. Please wait..."):
                logger.info(f"Querying database with query: {query}")
                try:
                    ctx = click.Context(process_query)
                    results = ctx.invoke(process_query, query=query)
                    
                    if not results:
                        st.warning("No results found for the query.")
                    else:
                        # Display results
                        st.success("Query completed!")
                        st.json(results)

                except Exception as e:
                    st.error(f"An error occurred: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Developed by Tau Group - Dheeraj**")
