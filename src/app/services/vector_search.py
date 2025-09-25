import logging
from typing import List, Dict, Optional, Any
from qdrant_client.http.models import (
    Filter, FieldCondition, MatchValue, Range, 
    SearchRequest, SearchParams
)

from ..core.qdrant_client import qdrant_manager
from .embedding_service import embedding_service

logger = logging.getLogger("vector-search")

class VectorSearchService:
    async def query(
        self,
        query_text: str,
        collection_name: str,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks based on vector similarity"""
        try:
            # Generate embedding for query
            embeddings = await embedding_service.get_embeddings([query_text])
            if not embeddings:
                return []
                
            query_embedding = embeddings[0]
            
            # Build filter if needed
            search_filter = None
            if filter_by:
                conditions = []
                for field, value in filter_by.items():
                    if isinstance(value, list):
                        # Handle range filters
                        if len(value) == 2:
                            conditions.append(
                                FieldCondition(
                                    key=field,
                                    range=Range(
                                        gte=value[0] if value[0] is not None else None,
                                        lte=value[1] if value[1] is not None else None
                                    )
                                )
                            )
                    else:
                        # Handle exact match
                        conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Execute search
            search_results = qdrant_manager.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter,
                with_payload=True,
                search_params=SearchParams(hnsw_ef=128)  # Increase for better recall
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload.get("content", ""),
                    "document_id": result.payload.get("document_id"),
                    "metadata": {
                        k: v for k, v in result.payload.items() 
                        if k not in ["content", "document_id"]
                    },
                    "score": result.score
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

vector_search = VectorSearchService()