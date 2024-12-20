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


def pdf_file_processor(folder_path, batch_size, queue, total_batches):
    logger.info("Starting PDF file processing...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    try:

        # List all files
        files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        batch_count = 0

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
                    batch_count += 1
                    print("Batch count: ", batch_count)

            # Add any remaining chunks
            if documents:
                queue.put((documents, metadatas, ids))
                batch_count += 1

        total_batches.value = batch_count
        
        # Signal end of production
        queue.put(None)
        logger.info("File processing complete.")
    except Exception as e:
        print(f"Error in producer: {e}")
        logger.error(f"Error in producer (file processing): {e}")
        queue.put(None)

def append_to_database(queue, progress, total_batches, use_cuda=False):

    processed_batches = 0
    queue_size = queue.qsize()
    embedding_model = get_embeddings()
    try:
        logger.info("Connecting to the database from consumer...")
        db = ChromaDBConnection(path=DB_PATH)
        collection = db.get_collection(COLLECTION_NAME, metadata={"hnsw:space": HNSW_SPACE})
        logger.info("Collection size: %d", collection.count())
    except Exception as e:
        print(f"Error connecting to database: {e}")
        logger.error(f"Error connecting to database from consumer: {e}")
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
                    processed_batches += 1
                    progress.value = (processed_batches / total_batches.value) * 100
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
    total_batches = mp.Value("i", 0)
    progress = mp.Value("d", 0)
    producer = mp.Process(target=pdf_file_processor, args=(paper_dir, BATCH_SIZE, queue, total_batches))
    consumer = mp.Process(target=append_to_database, args=(queue, progress, total_batches))

    # Start the processes
    producer.start()
    consumer.start()

    # Wait for the processes to finish
    producer.join()
    consumer.join()
    logger.info("Indexing pipeline completed.")

if __name__ == "__main__":
    main_function(PAPER_DIR, BATCH_SIZE)