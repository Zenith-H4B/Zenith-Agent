"""Embedding service using Google Gemini and FAISS."""
import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from loguru import logger
import google.generativeai as genai
from config import settings
from database.database import db
from bson import ObjectId


class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # FAISS index
        self.index = None
        self.embeddings_metadata = []
        self.dimension = 768  # Typical dimension for sentence embeddings
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata."""
        try:
            if os.path.exists(f"{settings.FAISS_INDEX_PATH}.index"):
                self.index = faiss.read_index(f"{settings.FAISS_INDEX_PATH}.index")
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
                
                # Load metadata
                if os.path.exists(f"{settings.EMBEDDINGS_PATH}_metadata.pkl"):
                    with open(f"{settings.EMBEDDINGS_PATH}_metadata.pkl", 'rb') as f:
                        self.embeddings_metadata = pickle.load(f)
                    logger.info(f"Loaded {len(self.embeddings_metadata)} metadata entries")
            else:
                logger.info("No existing FAISS index found, will create new one")
                
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            self.index = None
            self.embeddings_metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        try:
            os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
            os.makedirs(os.path.dirname(settings.EMBEDDINGS_PATH), exist_ok=True)
            
            if self.index:
                faiss.write_index(self.index, f"{settings.FAISS_INDEX_PATH}.index")
                logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
            
            # Save metadata
            with open(f"{settings.EMBEDDINGS_PATH}_metadata.pkl", 'wb') as f:
                pickle.dump(self.embeddings_metadata, f)
            logger.info(f"Saved {len(self.embeddings_metadata)} metadata entries")
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
    
    async def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text using Gemini."""
        try:
            # Use Gemini's embedding capability (Note: Gemini doesn't have direct embedding API)
            # We'll use a workaround by getting text representation and using sentence transformers
            from sentence_transformers import SentenceTransformer
            
            # Initialize sentence transformer model for embeddings
            if not hasattr(self, 'embedding_model'):
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self.embedding_model.encode(text)
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def add_to_index(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Add text and metadata to FAISS index."""
        try:
            embedding = await self.generate_embedding(text)
            if embedding is None:
                return False
            
            # Initialize index if not exists
            if self.index is None:
                self.index = faiss.IndexFlatL2(len(embedding))
                logger.info(f"Created new FAISS index with dimension {len(embedding)}")
            
            # Add to index
            embedding = embedding.reshape(1, -1)
            self.index.add(embedding)
            
            # Add metadata
            self.embeddings_metadata.append({
                'text': text,
                'metadata': metadata,
                'id': len(self.embeddings_metadata)
            })
            
            # Save index
            self._save_index()
            
            logger.info(f"Added text to index. Total vectors: {self.index.ntotal}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to index: {str(e)}")
            return False
    
    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar texts in the index."""
        try:
            if self.index is None or self.index.ntotal == 0:
                logger.warning("No vectors in index to search")
                return []
            
            query_embedding = await self.generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Search
            query_embedding = query_embedding.reshape(1, -1)
            distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
            
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx < len(self.embeddings_metadata):
                    result = self.embeddings_metadata[idx].copy()
                    result['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar texts for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []
    
    async def index_employee_skills(self, org_id: str) -> bool:
        """Index employee skills and capabilities for the organization."""
        try:
            # Get employees from database
            employees = list(db.users.find({ "org_id": ObjectId(org_id),
                "is_on_leave": "FALSE"}))
            
            for employee in employees:
                # Create skill text
                skills_text = f"Employee: {employee['name']}, Role: {employee['role']}, Skills: {', '.join(employee.get('skills', []))}"
                
                metadata = {
                    'type': 'employee_skills',
                    'employee_id': str(employee['_id']),
                    'org_id': org_id,
                    'employee_data': employee
                }
                
                await self.add_to_index(skills_text, metadata)
            
            logger.info(f"Indexed skills for {len(employees)} employees in org {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing employee skills: {str(e)}")
            return False
    
    async def find_suitable_employees(self, task_description: str, org_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """Find employees suitable for a task based on similarity search."""
        try:
            # Search for similar employee skills
            results = await self.search_similar(f"Task: {task_description}", k * 2)  # Get more results to filter
            
            # Filter for employees in the organization
            suitable_employees = []
            for result in results:
                if (result.get('metadata', {}).get('type') == 'employee_skills' and 
                    result.get('metadata', {}).get('org_id') == org_id):
                    suitable_employees.append(result)
                    if len(suitable_employees) >= k:
                        break
            
            logger.info(f"Found {len(suitable_employees)} suitable employees for task")
            return suitable_employees
            
        except Exception as e:
            logger.error(f"Error finding suitable employees: {str(e)}")
            return []


# Global embedding service instance
embedding_service = EmbeddingService()
