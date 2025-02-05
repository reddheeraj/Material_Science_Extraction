# Add these new imports at the top
import pandas as pd
import os
from LLM import get_embeddings
from db_connection import ChromaDBConnection
from config import DB_PATH, QUERY_LIMIT, COLLECTION_NAME, HNSW_SPACE, OUTPUT_DIR, TABLES_DIR
from logger import logger
from LLM import refine_with_llm
from typing import List, Dict
import json
import re
import click
from store_data import consolidate_to_json
from datetime import datetime

def retrieve_tables_for_page(source: str, page: int) -> str:
    """
    Retrieve tables for a specific page of a document and format them as Markdown.
    
    Args:
        source: Name of the source PDF file
        page: Page number from the metadata
        
    Returns:
        Formatted string containing all tables from the page
    """
    try:
        # Convert PDF filename to directory name
        paper_name = os.path.splitext(source)[0]
        tables_dir = os.path.join(TABLES_DIR, paper_name, f"page_{page}")
        
        if not os.path.exists(tables_dir):
            return ""
            
        tables = []
        for table_file in os.listdir(tables_dir):
            if table_file.endswith(".csv"):
                table_path = os.path.join(tables_dir, table_file)
                df = pd.read_csv(table_path)
                tables.append(df.to_markdown(index=False))
                logger.info(f"Table {table_file} retrieved.")
        
        return "\n\n".join([f"Table {i+1}:\n{t}" for i, t in enumerate(tables)])
    
    except Exception as e:
        logger.error(f"Error retrieving tables for {source} page {page}: {e}")
        return ""

def augment_chunks_with_tables(chunks: List[str], metadatas: List[Dict]) -> List[str]:
    """
    Enhance retrieved chunks with relevant tables from their source pages
    
    Args:
        chunks: List of retrieved text chunks
        metadatas: List of metadata dictionaries
        
    Returns:
        List of augmented chunks with tables appended
    """
    augmented_chunks = []
    
    for chunk, meta in zip(chunks, metadatas):
        try:
            tables = retrieve_tables_for_page(meta["source"], meta["page"])
            if tables:
                augmented = f"{chunk}\n\nDOCUMENT TABLES:\n{tables}"
                augmented_chunks.append(augmented)
                logger.info(f"Tables appended to chunk {meta['chunk_id']}")
            else:
                augmented_chunks.append(chunk)
        except KeyError:
            logger.warning("Missing metadata in chunk, skipping table augmentation")
            augmented_chunks.append(chunk)
    
    return augmented_chunks

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


# Modified process_query function
@click.command(name='query')
@click.option("--query")
def process_query(query):
    logger.info("Querying vector database...")
    chunks, metadatas = query_relevant_chunks(query)

    if not chunks or not metadatas:
        logger.warning("No results found for the query.")
        return

    # Augment chunks with tables before LLM processing
    logger.info("Augmenting chunks with relevant tables...")
    augmented_chunks = augment_chunks_with_tables(chunks, metadatas)
    
    logger.info("Refining with LLM...")
    print("Refining with LLM...")
    properties = refine_with_llm(augmented_chunks)  # Pass augmented chunks to LLM
    
    if not properties:
        logger.warning("LLM could not extract any properties.")
        return

    properties = parse_json_blocks(properties)

    # Combine results
    results = []
    for meta, prop in zip(metadatas, properties):
        results.append({
            "source": f"{meta['source']}, Page no: {meta['page']}",
            "chunk_id": meta["chunk_id"],
            "Properties": prop
        })
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"results_{timestamp}.json").replace("'", "\"").strip()
    results = consolidate_to_json(results, output_file)
    logger.info(f"Results saved to {output_file}")

    return results

if __name__ == "__main__":
    process_query()