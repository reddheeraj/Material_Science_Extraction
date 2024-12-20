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
        response_text = response['Properties']
        try:
            # Isolate the JSON part (handle responses with extra text)
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                print(f"Could not find JSON in response: {response_text}")
                logger.warning(f"Could not find JSON in response: {response_text}")
                continue

            # Parse the extracted JSON
            json_data = json.loads(json_match.group())
            # print("json data = ", json_data)
            json_data.update(new_info)

            consolidated_data.append(json_data)
        except Exception as e:
            print(f"Error processing response: {response}\n{e}")
            logger.error(f"Error processing response: {response_text}\n{e}")

    # # Write the consolidated data to a JSON file
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(consolidated_data, json_file, indent=4)

        print(f"Consolidated data saved to {json_file_path}")
        logger.info(f"Data saved to {json_file_path}")
    
    return consolidated_data

def display_results(results):
    flattened_data = []
    print(results[0])
    for data in results:
        row = {
            "Source": data["source"],
            "Chunk ID": data["chunk_id"],
            "Alloy": data["Alloy"],
            "Hardness": data["Properties"]["Hardness"],
            "Vickers Hardness": data["Properties"]["Vickers Hardness"],
            "Ultimate Tensile Strength": data["Properties"]["Ultimate Tensile Strength"],
            "Yield Strength": data["Properties"]["Yield Strength"],
            "Young Modulus": data["Properties"]["Young Modulus"],
            "Grain Size": data["Properties"]["Grain Size"],
            "Additional Information": data["Additional Information"]
        }
        flattened_data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(flattened_data)
    return df