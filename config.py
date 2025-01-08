import os

# General configurations
CASE = "Case1"
STUDY_DIR = "Studies"
PAPER_DIR = os.path.join(STUDY_DIR, CASE, "Papers")
OUTPUT_DIR = os.path.join(STUDY_DIR, CASE, "Outputs")
QUERY_DIR = os.path.join(STUDY_DIR, CASE, "Queries")
DB_PATH = "./chromadb"
COLLECTION_NAME = CASE
SUMMARY_DIR = os.path.join(STUDY_DIR, CASE, "Summary")

LOG_DIR = "logs"
MAIN_KEYWORDS = ["single phase", "homogenized", "homogeneity", "FCC",
    "high entropy alloys", "HEA", "properties"]

HARD_REQUIREMENTS = ["FCC structure", "Vacuum Arc Melter", "VAM"]
HARD_REJECTS = ["not homogeneous"]

PROPERTIES_TO_EXTRACT = [
    "hardness", "Vickers Hardness", "ultimate tensile strength",
    "yield strength", "young modulus", "grain size"
]

# LLM configurations
LLM_MODEL = "llama3.1:latest"
EMBEDDING_MODEL = "nomic-embed-text"

# Text splitter configurations
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 120
BATCH_SIZE = 10

# HNSW configurations
HNSW_SPACE = "cosine"

# Query configurations
QUERY_LIMIT = 5

# Prompt configurations
def prompt_template_A(chunk):
    PROMPT_TEMPLATE = f"""
You are an expert in materials science and materials properties. Your task is to analyze the given text and extract critical information in the following structured JSON format:
```json
{{
  "Alloy": "Name or description of the alloy, if mentioned",
  "Properties": {{
    "Hardness": "Value and unit, if mentioned",
    "Vickers Hardness": "Value and unit, if mentioned",
    "Ultimate Tensile Strength": "Value and unit, if mentioned",
    "Yield Strength": "Value and unit, if mentioned",
    "Young Modulus": "Value and unit, if mentioned",
    "Grain Size": "Value and unit, if mentioned"
  }},
  "Additional Information": "Summary of any other relevant details related to materials, testing, or experimental conditions"
}}
```

You must strictly adhere to the JSON format. If some values are missing, indicate them as null. Do not output anything other than a json output.
Here is the text for analysis: {chunk}
Extract the relevant information:
"""
    return PROMPT_TEMPLATE