import streamlit as st
from logger import logger
import click
from query_db import process_query
from store_data import display_results

def query_results():
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
                        
                        df = display_results(results)
                        st.subheader("Material Properties Data")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"An error occurred: {e}")