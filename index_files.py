import os
import time
from logger import logger
import multiprocessing as mp
from LLM import get_embeddings
from db_connection import ChromaDBConnection
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import PAPER_DIR, DB_PATH, COLLECTION_NAME, CHUNK_OVERLAP, CHUNK_SIZE, HNSW_SPACE, BATCH_SIZE

def transform_chunk(chunks):
    for chunk in chunks:
        chunk.page_content = str(chunk.page_content).strip()
        if not chunk.page_content:
            chunks.remove(chunk)
    return chunks


def pdf_file_processor(folder_path, batch_size, queue):
    logger.info("Starting PDF file processing...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    try:
        # queue = mp.Queue()

        # List all files
        files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]

        for file in files:
            pdf_path = os.path.join(folder_path, file)
            print(f"Processing file: {file}")
            logger.info(f"Processing file: {file}")
            
            # Load and split the PDF into chunks
            reader = PyPDFLoader(pdf_path)
            pages = reader.load()
            chunks = text_splitter.split_documents(pages)

            # Prepare batches for the queue
            documents, metadatas, ids = [], [], []
            for i, chunk in enumerate(chunks):
                documents.append(chunk.page_content)
                chunk.metadata['chunk_id'] = i
                metadatas.append(chunk.metadata)
                ids.append(f"{file}_{i}") ## use uuid instead

                if len(ids) >= batch_size:
                    queue.put((documents, metadatas, ids))
                    documents, metadatas, ids = [], [], []

            # Add any remaining chunks
            if documents:
                queue.put((documents, metadatas, ids))

        # Signal end of production
        queue.put(None)
        logger.info("File processing complete.")
    except Exception as e:
        print(f"Error in producer: {e}")
        logger.error(f"Error in producer (file processing): {e}")
        queue.put(None)

def append_to_database(queue, use_cuda=False):
    embedding_model = get_embeddings()
    db = ChromaDBConnection(path=DB_PATH)
    collection = db.get_collection(COLLECTION_NAME, metadata={"hnsw:space": HNSW_SPACE})
        # device = "cuda" if use_cuda else "cpu"
    try:    
        while True:
            batch = queue.get(timeout=30)
            if batch is None:
                print("Consumer received stop signal")
                logger.info("Received stop signal.")
                break
            else:
                print(f"Consumer processing batch of {len(batch[0])} items")

            try:
                logger.info(f"Processing batch of {len(batch[0])} documents.")
                collection.upsert(
                    ids=batch[2],
                    embeddings=[embedding_model.embed_query(doc) for doc in batch[0]],
                    documents=batch[0],
                    metadatas=batch[1]
                )
                print(f"Indexed batch with {len(batch[0])} documents.")
                logger.info(f"Indexed batch with {len(batch[0])} documents.")
            except Exception as e:
                print(f"Error adding batch to ChromaDB: {e}")
                logger.error(f"Error adding batch to ChromaDB: {e}")
    except Exception as e:
        print(f"Error in consumer: {e}")
        logger.error(f"Error in consumer: {e}")

def main_function(paper_dir, BATCH_SIZE=10):
    logger.info("Starting indexing pipeline...")

    # Set up multiprocessing
    queue = mp.Queue()
    producer = mp.Process(target=pdf_file_processor, args=(paper_dir, BATCH_SIZE, queue))
    consumer = mp.Process(target=append_to_database, args=(queue,))

    # Start the processes
    producer.start()
    consumer.start()

    # Wait for the processes to finish
    producer.join()
    consumer.join()
    logger.info("Indexing pipeline completed.")

if __name__ == "__main__":
    main_function(PAPER_DIR, BATCH_SIZE)