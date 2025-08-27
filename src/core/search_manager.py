"""
Search Manager for the Autonomous AI Assistant
Handles semantic search and retrieval operations with robust error handling and proper typing
"""
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Union, Mapping, cast
import numpy as np
import logging
from .cache_manager import CacheManager


# Type aliases for better clarity
Metadata = Dict[str, Union[str, int, float, bool, None]]
SearchMetadata = Dict[str, Any]


class SearchResult:
    """Data class for search results with proper type handling"""
    def __init__(self, id: str, text: str, metadata: SearchMetadata, distance: float):
        self.id = str(id)  # Ensure string type
        self.text = str(text) if text is not None else ""
        self.metadata = dict(metadata) if metadata else {}  # Convert to dict
        self.distance = float(distance) if distance is not None else 1.0
        self.similarity = max(0.0, 1.0 - self.distance)  # Ensure non-negative
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'text': self.text,
            'metadata': self.metadata,
            'distance': self.distance,
            'similarity': self.similarity
        }


class SearchManager:
    """Manages semantic search operations using sentence transformers"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.model_name = model_name
        self._embedding_dimension: Optional[int] = None
        
        try:
            # Initialize the sentence transformer model
            self.model = SentenceTransformer(model_name)
            # Get embedding dimension safely
            try:
                self._embedding_dimension = self.model.get_sentence_embedding_dimension()
            except AttributeError:
                # Fallback method for older versions
                test_embedding = self.model.encode("test")
                self._embedding_dimension = len(test_embedding) if test_embedding is not None else 384
            
            self.logger.info(f"Loaded sentence transformer model: {model_name} (dim: {self._embedding_dimension})")
        except Exception as e:
            self.logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        self.cache_manager = CacheManager()
        self._index_initialized = False
        
    def embed_text(self, text: str) -> List[float]:
        """Convert text to embedding vector with proper type handling"""
        if not text or not text.strip():
            self.logger.warning("Empty text provided for embedding")
            # Return zero vector with proper dimension
            dimension = self._embedding_dimension or 384
            return [0.0] * dimension
        
        try:
            embedding = self.model.encode(text.strip())
            # Ensure we return a list of floats
            if isinstance(embedding, np.ndarray):
                return embedding.astype(float).tolist()
            elif isinstance(embedding, list):
                return [float(x) for x in embedding]
            else:
                # Convert other types to list
                return list(map(float, embedding))
        except Exception as e:
            self.logger.error(f"Failed to embed text: {e}")
            # Return zero vector on error
            dimension = self._embedding_dimension or 384
            return [0.0] * dimension
    
    def add_to_search_index(self, text: str, metadata: Optional[SearchMetadata] = None) -> bool:
        """Add text to the search index with optional metadata"""
        if not text or not text.strip():
            self.logger.warning("Cannot index empty text")
            return False
            
        if metadata is None:
            metadata = {}
            
        try:
            embedding = self.embed_text(text)
            # Ensure metadata is properly typed
            safe_metadata: SearchMetadata = dict(metadata)  # Convert to dict
            safe_metadata['text'] = text
            safe_metadata['indexed_at'] = str(np.datetime64('now'))
            
            # Handle the cache manager return type properly
            result = self.cache_manager.add_vector(embedding, safe_metadata)
            
            # Handle None return type
            if result is None:
                self.logger.warning("Cache manager returned None for add_vector")
                return False
            
            success = bool(result)  # Ensure boolean type
            if success:
                self._index_initialized = True
                self.logger.debug(f"Successfully indexed text: {text[:50]}...")
            else:
                self.logger.warning(f"Failed to index text: {text[:50]}...")
            
            return success
        except Exception as e:
            self.logger.error(f"Error adding to search index: {e}")
            return False
            
    def semantic_search(self, query: str, n_results: int = 5) -> List[SearchResult]:
        """Perform semantic search on the indexed content with proper type handling"""
        if not query or not query.strip():
            self.logger.warning("Empty query provided for search")
            return []
        
        if not self._index_initialized:
            self.logger.warning("Search index is empty or not initialized")
            return []
        
        try:
            query_embedding = self.embed_text(query)
            results = self.cache_manager.query_vector(query_embedding, n_results)
            
            # Critical fix: Check if results is None or malformed
            if results is None:
                self.logger.warning("Cache manager returned None results")
                return []
            
            # Validate results structure
            if not isinstance(results, dict):
                self.logger.error(f"Invalid results type: {type(results)}")
                return []
            
            required_keys = ['ids', 'documents', 'metadatas', 'distances']
            missing_keys = [key for key in required_keys if key not in results]
            if missing_keys:
                self.logger.error(f"Missing keys in results: {missing_keys}")
                return []
            
            # Check if any of the required arrays are None
            for key in required_keys:
                if results[key] is None:
                    self.logger.error(f"Results['{key}'] is None")
                    return []
                
                # Check if it's a nested array and the first element exists
                if isinstance(results[key], list) and len(results[key]) > 0:
                    if results[key][0] is None:
                        self.logger.error(f"Results['{key}'][0] is None")
                        return []
            
            # Format results for easier consumption
            formatted_results: List[SearchResult] = []
            
            # Get the first batch of results (assuming batch structure)
            if (len(results['ids']) > 0 and len(results['ids'][0]) > 0):
                ids = results['ids'][0]
                documents = results['documents'][0] if results['documents'] else []
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                # Ensure all arrays have the same length
                min_length = min(len(ids), len(documents), len(metadatas), len(distances))
                
                for i in range(min_length):
                    try:
                        # Handle metadata type conversion properly
                        raw_metadata = metadatas[i] if i < len(metadatas) else {}
                        if raw_metadata is None:
                            safe_metadata: SearchMetadata = {}
                        elif isinstance(raw_metadata, dict):
                            # Convert Mapping to Dict[str, Any]
                            safe_metadata = {str(k): v for k, v in raw_metadata.items()}
                        else:
                            safe_metadata = {}
                        
                        search_result = SearchResult(
                            id=str(ids[i]) if ids[i] is not None else f"result_{i}",
                            text=str(documents[i]) if documents[i] is not None else "",
                            metadata=safe_metadata,
                            distance=float(distances[i]) if distances[i] is not None else 1.0
                        )
                        formatted_results.append(search_result)
                    except Exception as e:
                        self.logger.warning(f"Error formatting result {i}: {e}")
                        continue
            
            self.logger.info(f"Search completed: {len(formatted_results)} results for query '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    def batch_index(self, texts: List[str], metadatas: Optional[List[SearchMetadata]] = None) -> Dict[str, Any]:
        """Index multiple texts at once with proper type handling"""
        if not texts:
            self.logger.warning("No texts provided for batch indexing")
            return {"success": 0, "failed": 0, "errors": []}
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Ensure metadatas list matches texts length
        if len(metadatas) < len(texts):
            metadatas.extend([{}] * (len(texts) - len(metadatas)))
        
        success_count = 0
        failed_count = 0
        errors: List[str] = []
        
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            try:
                # Ensure metadata is properly typed
                safe_metadata = dict(metadata) if metadata else {}
                
                if self.add_to_search_index(text, safe_metadata):
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Failed to index item {i}: {text[:50]}...")
            except Exception as e:
                failed_count += 1
                errors.append(f"Error indexing item {i}: {str(e)}")
        
        result = {
            "success": success_count,
            "failed": failed_count,
            "errors": errors[:10]  # Limit error messages
        }
        
        self.logger.info(f"Batch indexing completed: {success_count} success, {failed_count} failed")
        return result
            
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index"""
        try:
            base_stats = self.cache_manager.get_stats()
            if base_stats is None:
                base_stats = {}
            
            stats = {
                **base_stats,
                "model_name": self.model_name,
                "embedding_dimension": self._embedding_dimension or 384,
                "index_initialized": self._index_initialized
            }
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting index stats: {e}")
            return {"error": str(e), "index_initialized": self._index_initialized}
    
    def clear_index(self) -> bool:
        """Clear the entire search index"""
        try:
            result = self.cache_manager.clear()
            # Handle None return type
            if result is None:
                success = False
                self.logger.warning("Cache manager clear returned None")
            else:
                success = bool(result)
            
            if success:
                self._index_initialized = False
                self.logger.info("Search index cleared successfully")
            else:
                self.logger.warning("Failed to clear search index")
            return success
        except Exception as e:
            self.logger.error(f"Error clearing index: {e}")
            return False
        
    def find_similar(self, text: str, threshold: float = 0.7, max_results: int = 10) -> List[SearchResult]:
        """Find similar texts based on semantic similarity threshold"""
        if not 0.0 <= threshold <= 1.0:
            self.logger.warning(f"Invalid threshold {threshold}, using 0.7")
            threshold = 0.7
        
        results = self.semantic_search(text, n_results=max_results)
        
        # Filter by similarity threshold (distance <= threshold means similarity >= 1-threshold)
        similar_results = [
            result for result in results 
            if result.distance <= (1.0 - threshold)
        ]
        
        self.logger.debug(f"Found {len(similar_results)} similar texts above threshold {threshold}")
        return similar_results
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the search manager"""
        health = {
            "status": "healthy",
            "issues": [],
            "model_loaded": False,
            "cache_manager_available": False,
            "index_initialized": self._index_initialized,
            "embedding_dimension": self._embedding_dimension
        }
        
        # Check model
        try:
            if self.model is not None:
                # Test embedding
                test_embedding = self.embed_text("test")
                if test_embedding and len(test_embedding) > 0:
                    health["model_loaded"] = True
                else:
                    health["issues"].append("Model embedding test failed")
        except Exception as e:
            health["issues"].append(f"Model error: {str(e)}")
        
        # Check cache manager
        try:
            if self.cache_manager is not None:
                cache_stats = self.cache_manager.get_stats()
                if cache_stats is not None:
                    health["cache_manager_available"] = True
                else:
                    health["issues"].append("Cache manager stats unavailable")
        except Exception as e:
            health["issues"].append(f"Cache manager error: {str(e)}")
        
        # Set overall status
        if health["issues"]:
            health["status"] = "degraded" if health["model_loaded"] else "unhealthy"
        
        return health
    
    def get_search_results_as_dicts(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get search results as dictionaries (backward compatibility)"""
        results = self.semantic_search(query, n_results)
        return [result.to_dict() for result in results]
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension safely"""
        return self._embedding_dimension or 384


# Type-safe utility functions
def convert_metadata(metadata: Union[Metadata, SearchMetadata, None]) -> SearchMetadata:
    """Convert metadata to SearchMetadata type safely"""
    if metadata is None:
        return {}
    
    # Convert to dict with Any values
    return {str(k): v for k, v in metadata.items()}


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_string_conversion(value: Any, default: str = "") -> str:
    """Safely convert value to string"""
    try:
        return str(value) if value is not None else default
    except Exception:
        return default


# Usage example with proper type handling
def example_usage():
    """Example usage of the SearchManager with proper error handling"""
    try:
        # Initialize search manager
        search_manager = SearchManager()
        
        # Check health before use
        health = search_manager.health_check()
        if health["status"] != "healthy":
            print(f"Search manager health issues: {health['issues']}")
            return
        
        # Index some sample data with proper typing
        sample_texts = [
            "How to open Chrome browser",
            "Steps to shutdown the computer",
            "Create a new document in Word",
            "Send an email to someone"
        ]
        
        sample_metadata: List[SearchMetadata] = [
            {"category": "browser", "action": "open", "priority": 1},
            {"category": "system", "action": "shutdown", "priority": 5},
            {"category": "document", "action": "create", "priority": 3},
            {"category": "communication", "action": "send", "priority": 2}
        ]
        
        # Batch index with proper types
        batch_result = search_manager.batch_index(sample_texts, sample_metadata)
        print(f"Batch indexing result: {batch_result}")
        
        # Perform search
        search_results = search_manager.semantic_search("open web browser", n_results=3)
        
        print("Search Results:")
        for result in search_results:
            print(f"- {result.text} (similarity: {result.similarity:.2f})")
        
        # Get statistics
        stats = search_manager.get_index_stats()
        print(f"Index stats: {stats}")
        
    except Exception as e:
        print(f"Example failed: {e}")


if __name__ == "__main__":
    example_usage()
