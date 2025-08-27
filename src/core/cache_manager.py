"""
Cache Manager for the Autonomous AI Assistant
Handles caching and persistent data storage
"""
import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Any
from chromadb import QueryResult, GetResult

class CacheManager:
    """Manages caching and persistent storage for semantic search vectors"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="chroma_db")
        # Always start with a fresh collection to avoid dimension mismatches
        try:
            self.client.delete_collection("semantic_search_vectors")
        except:
            pass
        self.collection = self.client.get_or_create_collection("semantic_search_vectors")
        
    def add_vector(self, vector: List[float], metadata: Dict[str, Any]):
        """Add a vector to the collection with associated metadata"""
        # Generate a unique ID for this entry
        entry_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[entry_id],
            documents=[metadata.get('text', '')],
            embeddings=[vector],
            metadatas=[metadata]
        )
        
    def query_vector(self, vector: List[float], n_results: int = 5) -> QueryResult:
        """Query the collection for similar vectors"""
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=n_results
        )
        return results
    
    def get_all_vectors(self) -> GetResult:
        """Retrieve all vectors from the collection"""
        return self.collection.get()
        
    def clear(self):
        """Clear the cache"""
        self.client.delete_collection("semantic_search_vectors")
        self.collection = self.client.get_or_create_collection("semantic_search_vectors")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        all_data = self.get_all_vectors()
        return {
            'total_vectors': len(all_data.get('ids', [])),
            'collection_name': self.collection.name
        }
