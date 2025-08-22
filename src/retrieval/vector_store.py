# Local Vector Store
import chromadb
import os
import logging
import numpy as np
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Union, cast, Tuple

import chromadb.types as ct

class LocalVectorStore:
    def __init__(self, collection_name: str = "local_docs", db_path: str = "db/vector_store"):
        """Initialize the local vector store with ChromaDB"""
        self.logger = logging.getLogger(__name__)
        self.collection_name = collection_name

        try:
            os.makedirs(db_path, exist_ok=True)
            # Use PersistentClient if available, else fallback to Client
            try:
                self.client = chromadb.PersistentClient(path=db_path)
            except AttributeError:
                self.client = chromadb.Client(Settings(persist_directory=db_path))
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Initialized vector store: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

    def _prepare_embeddings_and_metadatas(self, embeddings: List[List[float]],
                                         metadatas: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Convert embeddings and metadatas to ChromaDB-compatible formats"""
        embeddings_np = np.array(embeddings, dtype=np.float32)
        clean_metadatas: List[Dict[str, Any]] = []
        for md in metadatas:
            cleaned_md: Dict[str, Union[str, int, float, bool, None]] = {}
            for key, value in md.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    cleaned_md[key] = value
                else:
                    cleaned_md[key] = str(value)
            clean_metadatas.append(cleaned_md)
        embeddings_cast = embeddings_np  # np.ndarray is the expected type for embeddings
        metadatas_cast = clean_metadatas
        return embeddings_cast, metadatas_cast

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        if not documents:
            self.logger.warning("No documents provided to add")
            return False
        try:
            ids: List[str] = []
            embeddings: List[List[float]] = []
            metadatas: List[Dict[str, Any]] = []
            documents_text: List[str] = []
            has_embeddings = False

            for doc in documents:
                if "id" not in doc:
                    self.logger.error("Document missing required 'id' field")
                    continue
                ids.append(str(doc["id"]))
                if "embedding" in doc and doc["embedding"] is not None:
                    embeddings.append(doc["embedding"])
                    has_embeddings = True
                metadata = doc.get("metadata", {})
                cleaned_metadata: Dict[str, Any] = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        cleaned_metadata[key] = value
                    else:
                        cleaned_metadata[key] = str(value)[:500]
                metadatas.append(cleaned_metadata)
                if "content" in doc:
                    documents_text.append(str(doc["content"]))
                elif "text" in doc:
                    documents_text.append(str(doc["text"]))
                else:
                    documents_text.append(str(metadata.get("content", "")))

            if has_embeddings and len(embeddings) == len(ids):
                embeddings_cast, metadatas_cast = self._prepare_embeddings_and_metadatas(embeddings, metadatas)
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings_cast,
                    metadatas=cast(List[ct.Metadata], metadatas_cast),
                    documents=documents_text
                )
            else:
                metadatas_cast = cast(List[ct.Metadata], metadatas)
                self.collection.add(
                    ids=ids,
                    metadatas=metadatas_cast,
                    documents=documents_text
                )
            self.logger.info(f"Added {len(ids)} documents to collection")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False

    def _convert_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Convert ChromaDB metadata to standard dict format"""
        if isinstance(metadata, dict):
            return dict(metadata)
        return {}

    def query(self, query_text: Optional[str] = None, embedding: Optional[List[float]] = None,
              top_k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the vector store"""
        if not query_text and not embedding:
            self.logger.error("Either query_text or embedding must be provided")
            return []
        try:
            query_params: Dict[str, Any] = {"n_results": top_k}
            if where is not None:
                query_params["where"] = where
            if embedding is not None:
                embedding_np = np.array([embedding], dtype=np.float32)
                query_params["query_embeddings"] = embedding_np
            elif query_text is not None:
                query_params["query_texts"] = [query_text]
            results = self.collection.query(**query_params)
            formatted_results: List[Dict[str, Any]] = []

            ids_nested = results.get("ids")
            distances_nested = results.get("distances")
            metadatas_nested = results.get("metadatas")
            documents_nested = results.get("documents")

            ids_raw = ids_nested[0] if ids_nested and len(ids_nested) > 0 else []
            ids: List[str] = ids_raw if isinstance(ids_raw, list) else [ids_raw] if isinstance(ids_raw, str) else []
            distances: List[float] = distances_nested[0] if distances_nested and len(distances_nested) > 0 else []
            metadatas_raw = metadatas_nested[0] if metadatas_nested and len(metadatas_nested) > 0 else []
            documents_raw = documents_nested[0] if documents_nested and len(documents_nested) > 0 else []
            if isinstance(documents_raw, list):
                documents: List[str] = documents_raw
            elif isinstance(documents_raw, str):
                documents: List[str] = [documents_raw]
            else:
                documents: List[str] = []

            metadatas: List[Dict[str, Any]] = [
                self._convert_metadata(meta) for meta in metadatas_raw
            ]

            for i in range(len(ids)):
                result: Dict[str, Any] = {
                    "id": ids[i],
                    "distance": distances[i] if i < len(distances) else None,
                    "score": 1.0 - distances[i] if i < len(distances) else None,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "content": documents[i] if i < len(documents) else ""
                }
                formatted_results.append(result)
            self.logger.info(f"Query returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return []

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            self.logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            return False

    def update_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Update existing documents (delete and re-add)"""
        try:
            ids: List[str] = [str(doc["id"]) for doc in documents]
            self.delete_documents(ids)
            return self.add_documents(documents)
        except Exception as e:
            self.logger.error(f"Failed to update documents: {e}")
            return False

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Failed to get collection count: {e}")
            return 0

    def peek(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Peek at some documents in the collection"""
        try:
            results = self.collection.peek(limit=limit)
            formatted_results: List[Dict[str, Any]] = []
            ids_nested = results.get("ids")
            metadatas_nested = results.get("metadatas")
            documents_nested = results.get("documents")

            ids_raw = ids_nested[0] if ids_nested and len(ids_nested) > 0 else []
            ids: List[str] = ids_raw if isinstance(ids_raw, list) else [ids_raw] if isinstance(ids_raw, str) else []
            metadatas_raw = metadatas_nested[0] if metadatas_nested and len(metadatas_nested) > 0 else []
            documents_raw = documents_nested[0] if documents_nested and len(documents_nested) > 0 else []
            if isinstance(documents_raw, list):
                documents: List[str] = documents_raw
            elif isinstance(documents_raw, str):
                documents: List[str] = [documents_raw]
            else:
                documents: List[str] = []

            metadatas: List[Dict[str, Any]] = [
                self._convert_metadata(meta) for meta in metadatas_raw
            ]

            for i in range(len(ids)):
                result: Dict[str, Any] = {
                    "id": ids[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "content": documents[i] if i < len(documents) else ""
                }
                formatted_results.append(result)
            return formatted_results
        except Exception as e:
            self.logger.error(f"Peek failed: {e}")
            return []

    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            all_docs = self.collection.get()
            ids_nested = all_docs.get("ids")
            ids_raw = ids_nested[0] if ids_nested and len(ids_nested) > 0 else []
            if isinstance(ids_raw, list):
                ids = ids_raw
            elif isinstance(ids_raw, str):
                ids = [ids_raw]
            else:
                ids = []
            if ids:
                self.collection.delete(ids=ids)
            self.logger.info("Cleared all documents from collection")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            return False
