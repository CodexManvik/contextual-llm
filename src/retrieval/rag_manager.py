# Retrieval-Augmented Generation Manager
import os
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from .vector_store import LocalVectorStore

class RetrievalAugmentedGeneration:
    def __init__(self, embedder_model: str = 'all-MiniLM-L6-v2'):
        """Initialize RAG manager with embedder and vector store"""
        self.logger = logging.getLogger(__name__)
        
        try:
            self.embedder = SentenceTransformer(embedder_model)
            self.vector_store = LocalVectorStore()
            self.logger.info("Initialized RAG manager")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG manager: {e}")
            raise
    
    def index_local_files(self, directory: str) -> bool:
        """Index local files in the specified directory"""
        if not os.path.exists(directory):
            self.logger.error(f"Directory does not exist: {directory}")
            return False
        
        try:
            documents: List[Dict[str, Any]] = []
            for root, _, files in os.walk(directory):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            embedding = self.embedder.encode(content).tolist()
                            documents.append({
                                "id": path,
                                "embedding": embedding,
                                "metadata": {"path": path, "content": content[:500]}  # Snippet
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to process file {path}: {e}")
                        continue
            
            if not documents:
                self.logger.warning("No valid documents found to index")
                return False
            
            success = self.vector_store.add_documents(documents)
            if success:
                self.logger.info(f"Indexed {len(documents)} documents from {directory}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to index local files: {e}")
            return False
    
    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve context for the given query"""
        try:
            query_embedding = self.embedder.encode(query).tolist()
            results = self.vector_store.query(embedding=query_embedding, top_k=top_k)
            return [res["content"] for res in results if "content" in res]
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            return []
