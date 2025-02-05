import deepdoctection as dd
import pandas as pd
from io import StringIO
from IPython.core.display import HTML
from langchain_core.documents import Document
from logger import logger
import os
from config import CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE, DB_PATH, COLLECTION_NAME, HNSW_SPACE, PAPER_DIR, TABLES_DIR
from langchain_text_splitters import RecursiveCharacterTextSplitter
import multiprocessing as mp
from db_connection import ChromaDBConnection
from LLM import get_embeddings

def pdf_file_processor(folder_path, batch_size, queue, total_batches):
    logger.info("Starting PDF file processing...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    try:
        files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        batch_count = 0

        for file in files:
            pdf_path = os.path.join(folder_path, file)
            logger.info(f"Processing file: {file}")

            # Initialize deepdoctection analyzer
            analyzer = dd.get_dd_analyzer()
            df = analyzer.analyze(path=pdf_path)
            df.reset_state()
            doc = iter(df)

            # Prepare directories for tables
            paper_name = os.path.splitext(file)[0]
            tables_paper_dir = os.path.join(TABLES_DIR, paper_name)
            os.makedirs(tables_paper_dir, exist_ok=True)

            # Process each page
            all_docs = []
            for page_num, page in enumerate(doc, start=1):
                # Extract text from page (adjust based on deepdoctection's structure)
                text = page.text  # Verify the correct attribute/method for text extraction

                # Create Document with metadata
                metadata = {'source': file, 'page': page_num}
                all_docs.append(Document(page_content=text, metadata=metadata))

                # Extract and save tables
                if page.tables:
                    page_tables_dir = os.path.join(tables_paper_dir, f"page_{page_num}")
                    os.makedirs(page_tables_dir, exist_ok=True)

                    for table_idx, table in enumerate(page.tables):
                        try:
                            html_str = str(HTML(table.html).data)
                            df_table = pd.read_html(StringIO(html_str))[0]
                            csv_path = os.path.join(page_tables_dir, f"table_{table_idx}.csv")
                            df_table.to_csv(csv_path, index=False)
                        except Exception as e:
                            logger.error(f"Error processing table {table_idx} on page {page_num}: {e}")

            # Split each page's text into chunks
            chunks = text_splitter.split_documents(all_docs)

            # Prepare batches
            documents, metadatas, ids = [], [], []
            for i, chunk in enumerate(chunks):
                chunk_metadata = chunk.metadata.copy()
                chunk_metadata['chunk_id'] = i
                documents.append(chunk.page_content)
                metadatas.append(chunk_metadata)
                ids.append(f"{file}_{i}")

                if len(ids) >= batch_size:
                    queue.put((documents, metadatas, ids))
                    documents, metadatas, ids = [], [], []
                    batch_count += 1

            # Add remaining chunks
            if documents:
                queue.put((documents, metadatas, ids))
                batch_count += 1

        total_batches.value = batch_count
        queue.put(None)
        logger.info("File processing complete.")
    except Exception as e:
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
            batch = queue.get(block=True)
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
    ctx = mp.get_context("spawn")

    # Set up multiprocessing
    queue = ctx.Queue(maxsize=100)
    manager = ctx.Manager()
    total_batches = manager.Value("i", 0)
    progress = manager.Value("d", 0)
 
    producer = ctx.Process(target=pdf_file_processor, args=(paper_dir, BATCH_SIZE, queue, total_batches))
    consumer = ctx.Process(target=append_to_database, args=(queue, progress, total_batches))

    # Start the processes
    producer.start()
    consumer.start()

    # Wait for the processes to finish
    producer.join()
    consumer.join()
    logger.info("Indexing pipeline completed.")

if __name__ == "__main__":
    main_function(PAPER_DIR, BATCH_SIZE)