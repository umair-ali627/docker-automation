import logging
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from ..core.config import settings

logger = logging.getLogger("qdrant-client")

class QdrantManager:
    """Singleton class to manage Qdrant vector database connections"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QdrantManager, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Qdrant client"""
        if self._initialized:
            return

        qdrant_url = url or settings.QDRANT_URL
        qdrant_api_key = api_key or settings.QDRANT_API_KEY

        if not qdrant_url:
            raise ValueError("Qdrant URL must be provided or set in settings")

        try:
            self._client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key if qdrant_api_key else None,
                timeout=60
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    @property
    def client(self) -> QdrantClient:
        """Get the Qdrant client instance"""
        if not self._initialized:
            self.initialize()
        return self._client

    async def create_collection_if_not_exists(
        self, 
        collection_name: str,
        vector_size: int = 1536,
        distance: str = "Cosine"
    ) -> bool:
        """Create a Qdrant collection if it doesn't exist, and creates the payload index."""
        try:
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists")
                return False

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance[distance.upper()]
                )
            )
            logger.info(f"Created collection {collection_name}")

            # Create a payload index on the 'document_id' field.
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id", # <-- ALSO CORRECTED HERE FOR CONSISTENCY
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True
            )
            logger.info(f"Created payload index for 'document_id' on collection {collection_name}")

            return True
        except Exception as e:
            logger.error(f"Error creating collection or index for {collection_name}: {e}")
            raise

    async def delete_points_by_doc_id(self, collection_name: str, doc_id: str):
        """
        Deletes all vector points from a collection that match a specific document ID.
        """
        try:
            logger.info(f"Attempting to delete points for document_id '{doc_id}' from collection '{collection_name}'")
            
            # Verify points to delete
            points_before = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=doc_id))]  # Fixed key
                )
            )
            logger.info(f"Points found for deletion: {points_before}")

            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",  # Fixed key
                                match=models.MatchValue(value=doc_id),
                            )
                        ]
                    )
                ),
                wait=True
            )
            logger.info(f"Successfully deleted points for document_id '{doc_id}' from collection '{collection_name}'")

            # Verify deletion
            points_after = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=doc_id))]  # Fixed key
                )
            )
            logger.info(f"Points remaining after deletion: {points_after}")
        except UnexpectedResponse as e:
            logger.error(f"Unexpected response from Qdrant while deleting points for document_id {doc_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting points for document_id {doc_id}: {e}")
            raise

# Initialize singleton instance
qdrant_manager = QdrantManager()