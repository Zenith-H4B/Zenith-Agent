"""FAISS & MongoDB integration for embeddings."""

import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from loguru import logger
from config import settings
import hashlib
import pickle
import time

class EmbeddingManager:
    """Manages FAISS embeddings and MongoDB storage."""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client['myApp']
        self.embeddings_collection: Collection = self.db.embeddings
        self.metadata_collection: Collection = self.db.embedding_metadata
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.id_to_metadata = {}
        self.text_to_id = {}
        
        logger.info(f"EmbeddingManager initialized with dimension {embedding_dim}")
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URI}")
        
        # Load existing embeddings from MongoDB
        self._load_from_mongodb()
    
    def _generate_text_id(self, text: str) -> str:
        """Generate a unique ID for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _load_from_mongodb(self):
        """Load existing embeddings from MongoDB."""
        try:
            logger.info("Loading existing embeddings from MongoDB...")
            
            # Load metadata
            metadata_docs = list(self.metadata_collection.find())
            logger.debug(f"Found {len(metadata_docs)} metadata documents")
            
            # Load embeddings
            embedding_docs = list(self.embeddings_collection.find())
            logger.debug(f"Found {len(embedding_docs)} embedding documents")
            
            if embedding_docs:
                # Reconstruct FAISS index
                vectors = []
                for doc in embedding_docs:
                    embedding_data = doc['embedding']
                    if isinstance(embedding_data, list):
                        vector = np.array(embedding_data, dtype=np.float32)
                    else:
                        # If stored as binary
                        vector = pickle.loads(embedding_data)
                    
                    vectors.append(vector)
                    
                    # Restore metadata mapping
                    text_id = doc['text_id']
                    metadata = next((m for m in metadata_docs if m['text_id'] == text_id), {})
                    self.id_to_metadata[len(vectors) - 1] = {
                        'text_id': text_id,
                        'text': doc.get('text', ''),
                        'metadata': metadata
                    }
                    self.text_to_id[doc.get('text', '')] = len(vectors) - 1
                
                if vectors:
                    vectors_array = np.array(vectors, dtype=np.float32)
                    self.index.add(vectors_array)
                    logger.info(f"Loaded {len(vectors)} embeddings into FAISS index")
                    
        except Exception as e:
            logger.error(f"Error loading embeddings from MongoDB: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding index."""
        try:
            return {
                'total_embeddings': self.index.ntotal,
                'embedding_dimension': self.embedding_dim,
                'mongodb_embeddings': self.embeddings_collection.count_documents({}),
                'mongodb_metadata': self.metadata_collection.count_documents({}),
                'memory_mappings': len(self.text_to_id),
                'faiss_index_type': type(self.index).__name__
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}

# Global embedding manager instance
embedding_manager = EmbeddingManager()

# TODO: Implement FAISS and MongoDB integration
