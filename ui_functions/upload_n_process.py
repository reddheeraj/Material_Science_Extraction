import streamlit as st
import shutil
import os
import multiprocessing as mp
import time
from index_files import pdf_file_processor, append_to_database
from logger import logger
from config import PAPER_DIR, BATCH_SIZE

def upload_n_process():
    st.title("Upload Research Papers for Processing")
    st.write("Upload your PDF files, and the system will process them to index the content for semantic search.")

    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(PAPER_DIR, file.name)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
        st.success(f"Uploaded {len(uploaded_files)} file(s) successfully.")

    if st.button("Process Files"):
        total_batches = mp.Value('i', 0)
        progress = mp.Value("d", 0)
        with st.spinner("Indexing papers into the database. This might take a while..."):
            queue = mp.Queue()
            producer = mp.Process(target=pdf_file_processor, args=(PAPER_DIR, BATCH_SIZE, queue, total_batches))
            consumer = mp.Process(target=append_to_database, args=(queue, progress, total_batches))

            producer.start()
            consumer.start()
            
            # Display Streamlit progress bar
            progress_bar = st.progress(0)
            previous_progress = -1
            while consumer.is_alive():
                if progress.value != previous_progress:
                    progress_bar.progress(int(progress.value), text=f"Progress: {int(progress.value)}%")
                    previous_progress = progress.value
                time.sleep(0.5)

            if not consumer.is_alive():
                print("Consumer died...")
                logger.info("Consumer died...")

            producer.join()
            consumer.join()

        st.success("Processing completed! Your papers are now indexed for querying.")
