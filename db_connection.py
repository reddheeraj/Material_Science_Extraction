# Singleton class to manage connection to ChromaDB
import chromadb
from logger import logger

class ChromaDBConnection:
    _instance = None

    def __new__(cls, path):
        if cls._instance is None:
            logger.info("Creating new ChromaDB connection...")
            cls._instance = super(ChromaDBConnection, cls).__new__(cls)
            cls._instance.client = chromadb.PersistentClient(path=path)
        return cls._instance

    def get_collection(self, name, metadata):
        logger.info(f"Accessing collection: {name}")
        return self.client.get_or_create_collection(name=name, metadata=metadata)