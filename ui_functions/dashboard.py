import os
import json
import pandas as pd
import streamlit as st
from LLM import query_llama
from config import STUDY_DIR, CASE, OUTPUT_DIR

if not os.path.exists(os.path.join(STUDY_DIR, CASE, "summary")):
    os.makedirs(os.path.join(STUDY_DIR, CASE, "summary"))

# Function to merge JSON files
def merge_json_files(outputdir):
    all_data = []
    for file in os.listdir(outputdir):
        if file.endswith('.json'):
            with open(os.path.join(outputdir, file), 'r') as f:
                data = json.load(f)
                all_data.extend(data)
    return all_data

# Function to process data
def process_data(data):
    # Convert to DataFrame
    rows = []
    for item in data:
        row = {
            "Alloy": item.get("Alloy"),
            "Hardness": item["Properties"].get("Hardness"),
            "Vickers Hardness": item["Properties"].get("Vickers Hardness"),
            "Ultimate Tensile Strength": item["Properties"].get("Ultimate Tensile Strength"),
            "Yield Strength": item["Properties"].get("Yield Strength"),
            "Young Modulus": item["Properties"].get("Young Modulus"),
            "Additional Information": item.get("Additional Information"),
            "Source": item.get("source")
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Extract unique alloys and their counts
    alloy_counts = df["Alloy"].value_counts().reset_index()
    alloy_counts.columns = ["Alloy", "Count"]

    return df, alloy_counts

# Function to summarize data using LLM
def summarize_data(df):
    prompt = (
        "You are an assistant designed to analyze alloy datasets. Use the following structured approach to generate a summary:\n"
        "Step 1: Identify and list all unique alloy names from the dataset.\n"
        "Step 2: For each unique alloy, summarize the key properties (e.g., Hardness, Vickers Hardness, Yield Strength) and provide their values if available.\n"
        "Step 3: Analyze the 'Additional Information' column and provide a concise, aggregated summary of its content.\n"
        "Step 4: Ensure that the response is organized, precise, and adheres strictly to this format without deviating.\n"
        f"\nDataset:\n{df.to_string()}"
    )
    summary = query_llama(prompt)  # Assuming this function is implemented
    return summary

def dashboard():
    st.title("Alloy Analytics Dashboard")

    summary_dir = os.path.join(STUDY_DIR, CASE, "summary")
    if not os.path.exists(os.path.join(summary_dir, "summary.txt")):
        with st.spinner("Processing data..."):

            data = merge_json_files(OUTPUT_DIR)
            try:
                df, alloy_counts = process_data(data)

                summary = summarize_data(df)

                summary_dir = os.path.join(STUDY_DIR, CASE, "summary")
                df.to_json(os.path.join(summary_dir, "processed_data.json"), orient="records")
                with open(os.path.join(summary_dir, "summary.txt"), "w") as f:
                    f.write(summary)

                # Display analytics
                st.subheader("Unique Alloys")
                st.table(alloy_counts)

                st.subheader("Property Distributions")
                st.bar_chart(alloy_counts.set_index("Alloy"))

                st.subheader("Summary")
                st.write(summary)
            except:
                st.error("An Error occured.")
    else:
        df = pd.read_json(os.path.join(summary_dir, "processed_data.json"))
        alloy_counts = df["Alloy"].value_counts().reset_index()
        alloy_counts.columns = ["Alloy", "Count"]

        with open(os.path.join(summary_dir, "summary.txt"), "r") as f:
            summary = f.read()
        st.subheader("Unique Alloys")
        st.table(alloy_counts)

        st.subheader("Property Distributions")
        st.bar_chart(alloy_counts.set_index("Alloy"))

        st.subheader("Summary")
        st.write(summary)
