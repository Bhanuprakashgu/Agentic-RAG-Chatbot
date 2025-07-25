import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from config import Config
import logging

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.documents = []  # Store original documents with metadata
        self.dimension = None
        
    def initialize_index(self, dimension: int = None):
        """Initialize FAISS index"""
        if dimension is None:
            # Get dimension from model
            sample_embedding = self.model.encode(["sample text"])
            dimension = sample_embedding.shape[1]
        
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        logger.info(f"Initialized FAISS index with dimension {dimension}")
        
    def add_documents(self, chunks: List[str], metadata: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        if self.index is None:
            self.initialize_index()
        
        # Generate embeddings
        embeddings = self.model.encode(chunks)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents with metadata
        for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
            self.documents.append({
                'text': chunk,
                'metadata': meta,
                'id': len(self.documents)
            })
        
        logger.info(f"Added {len(chunks)} documents to vector store")
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                result['score'] = float(score)
                results.append(result)
        
        return results
    
    def save(self, path: str):
        """Save the vector store to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, f"{path}.index")
        
        # Save documents and metadata
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'model_name': self.model_name,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"Saved vector store to {path}")
    
    def load(self, path: str):
        """Load the vector store from disk"""
        try:
            # Load FAISS index
            if os.path.exists(f"{path}.index"):
                self.index = faiss.read_index(f"{path}.index")
            
            # Load documents and metadata
            if os.path.exists(f"{path}.pkl"):
                with open(f"{path}.pkl", 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.model_name = data['model_name']
                    self.dimension = data['dimension']
                    
                    # Reinitialize model if needed
                    if self.model_name != Config.EMBEDDING_MODEL:
                        self.model = SentenceTransformer(self.model_name)
            
            logger.info(f"Loaded vector store from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'model_name': self.model_name
        }

