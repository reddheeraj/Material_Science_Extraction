import os
import click
from logger import logger
from datetime import datetime
from store_data import consolidate_to_json
from db_connection import ChromaDBConnection
from LLM import refine_with_llm, get_embeddings
from config import QUERY_DIR, OUTPUT_DIR, DB_PATH, COLLECTION_NAME, QUERY_LIMIT, HNSW_SPACE


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
    # return results

@click.command(name='query')
@click.argument("query", type=str)
def process_query(query):
    click.echo("Querying vector database...")
    logger.info("Querying vector database...")
    chunks, metadatas = query_relevant_chunks(query)

    if not chunks or not metadatas:
        click.echo("No results found for the query.")
        logger.warning("No results found for the query.")
        return
    # print("metadatas: ", metadatas)
    logger.info("Refining with LLM...")
    print("Refining with LLM...")
    properties = refine_with_llm(chunks)
    if not properties:
        click.echo("LLM could not extract any properties.")
        logger.warning("LLM could not extract any properties.")
        return
    # print("properties: ", properties)
    # properties = ['a', 'b', 'c']

    # Combine results
    results = []
    for meta, prop in zip(metadatas, properties):
        # print("meta: ", meta)
    #     # print("prop: ", prop)
        results.append({"source": f"{meta["source"]}, Page no: {meta["page"]}", "chunk_id": meta["chunk_id"], "properties": prop})
    
    # Output results
    for result in results:
        print(f"Source: {result['source']}, Chunk: {result['chunk_id']}")
        print(f"Properties:\n{result['properties']}\n")
    
    # Consolidate results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"results_{timestamp}.json").replace("'", "\"").strip()
    consolidate_to_json(results, output_file)
    click.echo(f"Results saved to {output_file}")
    logger.info(f"Results saved to {output_file}")
    
    return results

if __name__ == "__main__":
    process_query()
