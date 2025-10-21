from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""
    
    @abstractmethod
    async def upsert_vectors(
        self,
        vectors: List[tuple],
        namespace: str,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Insert or update vectors in the vector store.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            namespace: Namespace for tenant isolation (typically project_id)
            metadata: Optional list of metadata dictionaries for each vector
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        query_vector: List[float],
        namespace: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors.
        
        Args:
            query_vector: Query vector
            namespace: Namespace to search in (typically project_id)
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of results with id, score, and metadata
        """
        pass
    
    @abstractmethod
    async def delete(self, vector_ids: List[str], namespace: str) -> bool:
        """
        Delete vectors by IDs.
        
        Args:
            vector_ids: List of vector IDs to delete
            namespace: Namespace (typically project_id)
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def delete_namespace(self, namespace: str) -> bool:
        """
        Delete an entire namespace (e.g., when deleting a project).
        
        Args:
            namespace: Namespace to delete (typically project_id)
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_index_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Args:
            namespace: Optional namespace to get stats for
            
        Returns:
            Dictionary with index statistics
        """
        pass


class PineconeVectorStore(BaseVectorStore):
    """Pinecone vector store implementation."""
    
    def __init__(self):
        """Initialize Pinecone client."""
        if not settings.pinecone_api_key:
            raise ValueError("Pinecone API key not configured")
        
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            # Initialize Pinecone (v5.x API)
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Get or create index
            index_name = settings.pinecone_index_name
            
            # Check if index exists
            existing_indexes = [idx['name'] for idx in self.pc.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {index_name}")
                # Create index with serverless spec
                self.pc.create_index(
                    name=index_name,
                    dimension=settings.embedding_dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Created Pinecone index: {index_name}")
            
            # Connect to index
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            raise
    
    async def upsert_vectors(
        self,
        vectors: List[tuple],
        namespace: str,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Upsert vectors to Pinecone.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            namespace: Namespace for tenant isolation
            metadata: Optional metadata (already included in tuples)
        """
        try:
            # Pinecone expects format: [(id, values, metadata), ...]
            self.index.upsert(vectors=vectors, namespace=namespace)
            logger.info(f"Upserted {len(vectors)} vectors to namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting vectors to Pinecone: {str(e)}")
            raise
    
    async def query(
        self,
        query_vector: List[float],
        namespace: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for similar vectors.
        """
        try:
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "namespace": namespace,
                "include_metadata": True
            }
            
            if filter_dict:
                query_params["filter"] = filter_dict
            
            results = self.index.query(**query_params)
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.info(f"Query returned {len(formatted_results)} results from namespace {namespace}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            raise
    
    async def delete(self, vector_ids: List[str], namespace: str) -> bool:
        """Delete vectors from Pinecone."""
        try:
            self.index.delete(ids=vector_ids, namespace=namespace)
            logger.info(f"Deleted {len(vector_ids)} vectors from namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors from Pinecone: {str(e)}")
            return False
    
    async def delete_namespace(self, namespace: str) -> bool:
        """Delete entire namespace from Pinecone."""
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting namespace from Pinecone: {str(e)}")
            return False
    
    async def get_index_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        try:
            stats = self.index.describe_index_stats()
            
            if namespace:
                namespace_stats = stats.namespaces.get(namespace, {})
                return {
                    "namespace": namespace,
                    "vector_count": namespace_stats.get("vector_count", 0)
                }
            else:
                return {
                    "total_vector_count": stats.total_vector_count,
                    "dimension": stats.dimension,
                    "namespaces": {
                        ns: {"vector_count": info.vector_count}
                        for ns, info in stats.namespaces.items()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting index stats from Pinecone: {str(e)}")
            raise


def get_vector_store() -> BaseVectorStore:
    """
    Factory function to get the appropriate vector store client.
    Currently returns Pinecone client, but can be extended
    to support other vector stores (Weaviate, Qdrant, pgvector, etc.)
    """
    return PineconeVectorStore()

