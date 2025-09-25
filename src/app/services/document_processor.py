import os
import tempfile
import logging
from typing import List, Dict, Any, Tuple, Optional, BinaryIO
import uuid
import asyncio
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
)

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.document import Document, KnowledgeBase
from ..crud.crud_documents import crud_document, document_service, crud_knowledge_base
from ..core.qdrant_client import qdrant_manager
from .embedding_service import embedding_service

from sqlalchemy import update, func
from qdrant_client.http import models

logger = logging.getLogger("document-processor")

class DocumentProcessor:
    def __init__(self):
        # Adjust chunking strategy for large documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks for better retrieval
            chunk_overlap=50,  # Reduced overlap for more efficient storage
            length_function=len,
        )
        
        # Add a separate splitter for really large documents
        self.large_doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
    

    async def process_file(
        self, 
        db: AsyncSession,
        file: BinaryIO, 
        filename: str, 
        knowledge_base_id: int
    ) -> Document:
        """Process a file upload and store in the database with embeddings"""
        # Detect content type
        content_type = self._get_content_type(filename)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file.read())
            temp_path = temp_file.name
        
        try:
            # Get knowledge base
            kb = await crud_knowledge_base.get(db=db, id=knowledge_base_id)
            if not kb:
                raise ValueError(f"Knowledge base with ID {knowledge_base_id} not found")
            
            # Check if document with same filename already exists in this knowledge base
            from sqlalchemy import select
            stmt = select(Document).where(
                (Document.filename == filename) & 
                (Document.knowledge_base_id == knowledge_base_id)
            )
            result = await db.execute(stmt)
            existing_doc = result.scalar_one_or_none()
            
            # Extract text based on file type
            text = await self._extract_text(temp_path, content_type)

            if len(text) > 1000000:  # 1MB of text
                logger.info(f"Large document detected ({len(text)} chars), using large document chunking")
                chunks = self.large_doc_splitter.split_text(text)
            else:
                chunks = self.text_splitter.split_text(text)
            
            # Create or update document
            if existing_doc:
                logger.info(f"Document '{filename}' already exists in KB {knowledge_base_id}, updating")
                # Use update_direct to avoid querying for the object again
                from ..schemas.document import DocumentUpdateInternal
                await db.execute(
                    update(Document)
                    .where(Document.id == existing_doc.id)
                    .values(
                        content=text,
                        updated_at=func.now()
                    )
                )
                await db.commit()
                document = existing_doc
                
                # Remove existing chunks from Qdrant if they exist
                try:
                    filter_by = {"document_id": document.id}
                    qdrant_manager.client.delete(
                        collection_name=kb["qdrant_collection"],
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="document_id",
                                        match=models.MatchValue(value=document.id)
                                    )
                                ]
                            )
                        )
                    )
                    logger.info(f"Removed existing chunks for document {document.id}")
                except Exception as e:
                    logger.warning(f"Error removing existing chunks: {e}")
            else:
                # Create new document
                from ..schemas.document import DocumentCreateInternal
                doc_in = DocumentCreateInternal(
                    filename=filename,
                    content_type=content_type,
                    content=text,
                    knowledge_base_id=knowledge_base_id,
                    chunk_count=0  # Will update after processing
                )
                document = await crud_document.create(db=db, object=doc_in)
            
            # Split into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Get embeddings for chunks
            embeddings = await embedding_service.get_embeddings(chunks)
            
            # Store chunks with embeddings in Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create a unique ID for each point
                point_id = uuid.uuid4()
                
                # Prepare payload with text and metadata
                payload = {
                    "content": chunk,
                    "document_id": document.id,
                    "chunk_index": i,
                    "filename": filename,
                    "content_type": content_type
                }
                
                points.append({
                    "id": str(point_id),
                    "vector": embedding,
                    "payload": payload
                })
            
            # Upload in batches of 100 points
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                qdrant_manager.client.upsert(
                    collection_name=kb["qdrant_collection"],
                    points=batch
                )
            
            # Update document with chunk count - using direct SQL to avoid the multiple results issue
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(chunk_count=len(chunks))
            )
            await db.commit()
            
            # Refresh document from database
            await db.refresh(document)
            
            logger.info(f"Processed document '{filename}' with {len(chunks)} chunks")
            return document
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext == '.txt':
            return 'text/plain'
        elif ext in ['.doc', '.docx']:
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext == '.csv':
            return 'text/csv'
        else:
            return 'application/octet-stream'
    
    async def _extract_text(self, file_path: str, content_type: str) -> str:
        """Extract text from file based on content type"""
        try:
            if content_type == 'application/pdf':
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                return "\n\n".join(doc.page_content for doc in docs)
            
            elif content_type == 'text/plain':
                loader = TextLoader(file_path)
                docs = loader.load()
                return "\n\n".join(doc.page_content for doc in docs)
                
            elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
                return "\n\n".join(doc.page_content for doc in docs)
                
            elif content_type == 'text/csv':
                loader = CSVLoader(file_path)
                docs = loader.load()
                return "\n\n".join(doc.page_content for doc in docs)
                
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise

document_processor = DocumentProcessor()