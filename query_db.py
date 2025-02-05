from LLM import get_embeddings
from db_connection import ChromaDBConnection
from config import DB_PATH, QUERY_LIMIT, COLLECTION_NAME, HNSW_SPACE, OUTPUT_DIR
from logger import logger
from LLM import refine_with_llm
from typing import List, Dict
import re
import json

import os
import click
from store_data import consolidate_to_json
from datetime import datetime

def parse_json_blocks(texts: List[str]) -> List[Dict]:
    """
    Extract and parse JSON data from text blocks formatted with ```json ... ```
    
    Args:
        texts: List of strings containing potential JSON blocks
        
    Returns:
        List of parsed JSON dictionaries
    """
    parsed_data = []
    json_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    
    for text in texts:
        # Find all JSON blocks in the text
        json_blocks = json_pattern.findall(text)
        
        for json_str in json_blocks:
            try:
                # Clean and parse the JSON
                cleaned = json_str.strip()
                parsed = json.loads(cleaned)
                parsed_data.append(parsed)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}\nProblematic JSON:\n{json_str}")
                
    return parsed_data


def query_relevant_chunks(query):
    # Compute query embedding
    logger.info("Computing query embedding...")
    embedding_model = get_embeddings()
    query_embedding = embedding_model.embed_query(query)
    
    # Retrieve top n relevant chunks
    logger.info("Connecting to the database...")
    db = ChromaDBConnection(path=DB_PATH)
    try:
        collection = db.get_collection(name=COLLECTION_NAME, metadata={"hnsw:space": HNSW_SPACE})
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=QUERY_LIMIT
        )
        logger.info("Query successful.")
        # print(results)
        return results["documents"][0], results["metadatas"][0]
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Error querying database: {e}")
        return None, None

# chunks, metadata = query_relevant_chunks("tensile strength")

# print("chunks = ", chunks)

@click.command(name='query')
@click.option("--query")
def process_query(query):
    # click.echo("Querying vector database...")
    logger.info("Querying vector database...")
    chunks, metadatas = query_relevant_chunks(query)

    if not chunks or not metadatas:
        # click.echo("No results found for the query.")
        logger.warning("No results found for the query.")
        return
    # print("metadatas: ", metadatas)
    logger.info("Refining with LLM...")
    print("Refining with LLM...")
    properties = refine_with_llm(chunks)
    if not properties:
        # click.echo("LLM could not extract any properties.")
        logger.warning("LLM could not extract any properties.")
        return
    # print("properties: ", properties)
    # properties = ['a', 'b', 'c']

    # add a properties clean up function here
    properties = parse_json_blocks(properties)

    
    # Combine results
    results = []
    for meta, prop in zip(metadatas, properties):
        # print("meta: ", meta)
    #     # print("prop: ", prop)
        results.append({"source": f"{meta['source']}, Page no: {meta['page']}", "chunk_id": meta["chunk_id"], "Properties": prop})
    
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"results_{timestamp}.json").replace("'", "\"").strip()
    results = consolidate_to_json(results, output_file)
    logger.info(f"Results saved to {output_file}")

    return results

if __name__ == "__main__":
    process_query()