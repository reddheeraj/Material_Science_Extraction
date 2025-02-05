import json
import re
from logger import logger
import pandas as pd

def consolidate_to_json(results, json_file_path):
    """
    Processes a list of LLM responses and consolidates them into a single JSON file.

    Args:
        results (list): List of JSON-like response strings from the LLM for each chunk.
        json_file_path (str): Path to save the resulting JSON file.
    """
    logger.info("Consolidating data to JSON...")
    consolidated_data = []
    response = results[0]
    for response in results:
        new_info = {
            "source": response['source'],
            "chunk_id": response['chunk_id']
        }
        response_properties = response['Properties']
        try:
            if isinstance(response_properties, dict):  # Ensure it's a dict
                response_properties.update(new_info)
                consolidated_data.append(response_properties)
            else:
                logger.warning(f"Expected dictionary for Properties, but got {type(response_properties)}")
        except Exception as e:
            print(f"Error processing response: {response}\n{e}")
            logger.error(f"Error processing response: {response}\n{e}")

    # # Write the consolidated data to a JSON file
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(consolidated_data, json_file, indent=4)

        print(f"Consolidated data saved to {json_file_path}")
        logger.info(f"Data saved to {json_file_path}")
    
    return consolidated_data

def display_results(results):
    flattened_data = []
    # print(results[0])
    for data in results:
        row = {
            "Source": data["source"],
            "Chunk ID": data["chunk_id"],
            "Alloy": data["Alloy"] if "Alloy" in data else None
        }
        for key, value in data["Properties"].items():
            row[key] = value
        if "Additional Information" in data:
            row["Additional Information"] = data["Additional Information"]
        flattened_data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(flattened_data)
    # position the additional information column at the end
    if "Additional Information" in df.columns:
        cols = list(df.columns)
        cols.remove("Additional Information")
        cols.append("Additional Information")
        df = df[cols]
    return df