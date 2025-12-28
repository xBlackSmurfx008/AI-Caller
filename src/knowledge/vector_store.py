"""Vector database abstraction layer"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

from src.utils.config import get_settings
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorStoreType(str, Enum):
    """Vector store type enumeration"""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"


class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store"""
        pass

    @abstractmethod
    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Upsert vectors into the store
        
        Args:
            vectors: List of embedding vectors
            ids: List of vector IDs
            metadata: Optional metadata for each vector
            namespace: Optional namespace
        """
        pass

    @abstractmethod
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Optional namespace
            filter: Optional metadata filter
            
        Returns:
            List of results with id, score, and metadata
        """
        pass

    @abstractmethod
    async def delete(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> None:
        """
        Delete vectors by IDs
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
        """
        pass


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation"""

    def __init__(self):
        """Initialize Pinecone store"""
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None

    async def initialize(self) -> None:
        """Initialize Pinecone"""
        try:
            import pinecone

            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT,
            )

            # Get or create index
            if self.index_name not in pinecone.list_indexes():
                # Create index if it doesn't exist
                pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                )

            self.index = pinecone.Index(self.index_name)
            logger.info("pinecone_initialized", index_name=self.index_name)

        except Exception as e:
            logger.error("pinecone_init_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to initialize Pinecone: {str(e)}") from e

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert vectors to Pinecone"""
        if not self.index:
            await self.initialize()

        try:
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for i, (vector, vector_id) in enumerate(zip(vectors, ids)):
                vector_data = {
                    "id": vector_id,
                    "values": vector,
                }
                if metadata and i < len(metadata):
                    vector_data["metadata"] = metadata[i]
                vectors_to_upsert.append(vector_data)

            self.index.upsert(
                vectors=vectors_to_upsert,
                namespace=namespace,
            )

            logger.debug("pinecone_upserted", count=len(vectors), namespace=namespace)

        except Exception as e:
            logger.error("pinecone_upsert_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to upsert to Pinecone: {str(e)}") from e

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query Pinecone"""
        if not self.index:
            await self.initialize()

        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=True,
            )

            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {}),
                }
                for match in results.get("matches", [])
            ]

        except Exception as e:
            logger.error("pinecone_query_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to query Pinecone: {str(e)}") from e

    async def delete(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> None:
        """Delete from Pinecone"""
        if not self.index:
            await self.initialize()

        try:
            self.index.delete(ids=ids, namespace=namespace)
            logger.debug("pinecone_deleted", count=len(ids), namespace=namespace)

        except Exception as e:
            logger.error("pinecone_delete_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to delete from Pinecone: {str(e)}") from e


class WeaviateVectorStore(VectorStore):
    """Weaviate vector store implementation"""

    def __init__(self):
        """Initialize Weaviate store"""
        self.client = None
        self.class_name = "KnowledgeEntry"

    async def initialize(self) -> None:
        """Initialize Weaviate"""
        try:
            import weaviate

            self.client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None,
            )

            # Create schema if it doesn't exist
            if not self.client.schema.exists(self.class_name):
                schema = {
                    "class": self.class_name,
                    "description": "Knowledge base entries",
                    "vectorizer": "none",  # We provide our own vectors
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                        },
                        {
                            "name": "title",
                            "dataType": ["string"],
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                        },
                        {
                            "name": "business_id",
                            "dataType": ["string"],
                        },
                    ],
                }
                self.client.schema.create_class(schema)

            logger.info("weaviate_initialized", class_name=self.class_name)

        except Exception as e:
            logger.error("weaviate_init_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to initialize Weaviate: {str(e)}") from e

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert vectors to Weaviate"""
        if not self.client:
            await self.initialize()

        try:
            with self.client.batch as batch:
                for i, (vector, vector_id) in enumerate(zip(vectors, ids)):
                    properties = metadata[i] if metadata and i < len(metadata) else {}
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.class_name,
                        uuid=vector_id,
                        vector=vector,
                    )

            logger.debug("weaviate_upserted", count=len(vectors))

        except Exception as e:
            logger.error("weaviate_upsert_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to upsert to Weaviate: {str(e)}") from e

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query Weaviate"""
        if not self.client:
            await self.initialize()

        try:
            query = self.client.query.get(
                self.class_name,
                ["content", "title", "source", "business_id"],
            ).with_near_vector({
                "vector": query_vector,
            }).with_limit(top_k)

            if filter:
                # Apply filter if provided
                # Weaviate uses GraphQL where filters
                pass  # Simplified for now

            results = query.do()

            return [
                {
                    "id": result.get("_additional", {}).get("id"),
                    "score": result.get("_additional", {}).get("certainty", 0),
                    "metadata": {k: v for k, v in result.items() if k != "_additional"},
                }
                for result in results.get("data", {}).get("Get", {}).get(self.class_name, [])
            ]

        except Exception as e:
            logger.error("weaviate_query_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to query Weaviate: {str(e)}") from e

    async def delete(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> None:
        """Delete from Weaviate"""
        if not self.client:
            await self.initialize()

        try:
            for vector_id in ids:
                self.client.data_object.delete(
                    uuid=vector_id,
                    class_name=self.class_name,
                )

            logger.debug("weaviate_deleted", count=len(ids))

        except Exception as e:
            logger.error("weaviate_delete_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to delete from Weaviate: {str(e)}") from e


class ChromaVectorStore(VectorStore):
    """Chroma vector store implementation"""

    def __init__(self):
        """Initialize Chroma store"""
        self.client = None
        self.collection_name = "knowledge_base"

    async def initialize(self) -> None:
        """Initialize Chroma"""
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            logger.info("chroma_initialized", collection_name=self.collection_name)

        except Exception as e:
            logger.error("chroma_init_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to initialize Chroma: {str(e)}") from e

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert vectors to Chroma"""
        if not self.collection:
            await self.initialize()

        try:
            # Chroma expects metadata as a list of dicts
            metadatas = metadata if metadata else [{}] * len(ids)

            self.collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
            )

            logger.debug("chroma_upserted", count=len(vectors))

        except Exception as e:
            logger.error("chroma_upsert_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to upsert to Chroma: {str(e)}") from e

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query Chroma"""
        if not self.collection:
            await self.initialize()

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=filter,
            )

            return [
                {
                    "id": results["ids"][0][i],
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                }
                for i in range(len(results["ids"][0]))
            ]

        except Exception as e:
            logger.error("chroma_query_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to query Chroma: {str(e)}") from e

    async def delete(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> None:
        """Delete from Chroma"""
        if not self.collection:
            await self.initialize()

        try:
            self.collection.delete(ids=ids)
            logger.debug("chroma_deleted", count=len(ids))

        except Exception as e:
            logger.error("chroma_delete_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to delete from Chroma: {str(e)}") from e


def get_vector_store(store_type: Optional[str] = None) -> VectorStore:
    """
    Get vector store instance based on configuration
    
    Args:
        store_type: Optional store type override
        
    Returns:
        VectorStore instance
    """
    # Determine store type from settings
    if store_type:
        type_enum = VectorStoreType(store_type)
    elif settings.PINECONE_API_KEY:
        type_enum = VectorStoreType.PINECONE
    elif settings.WEAVIATE_API_KEY:
        type_enum = VectorStoreType.WEAVIATE
    else:
        type_enum = VectorStoreType.CHROMA  # Default to Chroma

    if type_enum == VectorStoreType.PINECONE:
        return PineconeVectorStore()
    elif type_enum == VectorStoreType.WEAVIATE:
        return WeaviateVectorStore()
    else:
        return ChromaVectorStore()

