# import io
# import logging

# from typing import List, Optional, Any
# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
# from sqlalchemy.ext.asyncio import AsyncSession
# import uuid as uuid_pkg

# from ...core.db.database import async_get_db
# from ...models.document import KnowledgeBase, Document
# from ...schemas.document import (
#     KnowledgeBaseRead, DocumentRead, KnowledgeBaseCreate
# )
# from ...crud.crud_documents import document_service, crud_document, crud_knowledge_base
# from ...services.document_processor import document_processor
# from ...api.dependencies import get_current_user
# from ...models.user import User

# router = APIRouter(tags=["knowledge-base"])
# logger = logging.getLogger("api-knowledge-base")


# @router.post("/knowledge-base", response_model=KnowledgeBaseRead)
# async def create_knowledge_base(
#     kb_create: KnowledgeBaseCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Create a new knowledge base"""
#     kb = await document_service.create_knowledge_base(
#         db=db,
#         name=kb_create.name,
#         description=kb_create.description,
#         owner_id=current_user["id"]
#     )
#     return kb

# @router.get("/knowledge-base", response_model=List[KnowledgeBaseRead])
# async def list_knowledge_bases(
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """List all knowledge bases for the current user"""
#     kbs = await document_service.get_knowledge_bases_by_owner(
#         db=db, owner_id=current_user["id"]
#     )
#     return kbs



# @router.post("/knowledge-base/{kb_id}/upload", response_model=DocumentRead)
# async def upload_document(
#     kb_id: uuid_pkg.UUID,
#     file: UploadFile = File(...),
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Upload and process a document for a knowledge base"""
#     # Check file size
#     file_size = 0
#     chunk_size = 1024 * 1024  # 1MB
#     content = b''
    
#     # Read file in chunks to avoid memory issues
#     while chunk := await file.read(chunk_size):
#         content += chunk
#         file_size += len(chunk)
#         if file_size > 50 * 1024 * 1024:  # 50MB limit
#             raise HTTPException(
#                 status_code=413, 
#                 detail="File too large. Maximum size is 50MB."
#             )
    
#     # Check if knowledge base exists and belongs to user
#     kb = await crud_knowledge_base.get(db=db, id=kb_id)
#     if not kb:
#         raise HTTPException(status_code=404, detail="Knowledge base not found")
        
#     if kb["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
#     # Create a file-like object from the content
#     file_obj = io.BytesIO(content)
    
#     # Process document
#     try:
#         document = await document_processor.process_file(
#             db=db,
#             file=file_obj,
#             filename=file.filename,
#             knowledge_base_id=kb_id
#         )
#         return document
#     except Exception as e:
#         logger.exception(f"Error processing document: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing document: {str(e)}"
#         )
    
# @router.get("/knowledge-base/{kb_id}/documents", response_model=List[DocumentRead])
# async def list_documents(
#     kb_id: uuid_pkg.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """List all documents in a knowledge base"""
#     # Check if knowledge base exists and belongs to user
#     kb = await crud_knowledge_base.get(db=db, id=kb_id)
#     if not kb:
#         raise HTTPException(status_code=404, detail="Knowledge base not found")
        
#     if kb["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
#     documents = await document_service.get_documents_by_knowledge_base(
#         db=db, kb_id=kb_id
#     )
    
#     return documents

# @router.get("/knowledge-base/{kb_id}/query")
# async def query_knowledge_base(
#     kb_id: uuid_pkg.UUID,
#     q: str,
#     limit: int = 5,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Query a knowledge base with vector search"""
#     from ...services.vector_search import vector_search
    
#     # Check if knowledge base exists and belongs to user
#     kb = await crud_knowledge_base.get(db=db, id=kb_id)
#     if not kb:
#         raise HTTPException(status_code=404, detail="Knowledge base not found")
        
#     if kb["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
#     # Perform vector search
#     results = await vector_search.query(
#         query_text=q,
#         collection_name=kb["qdrant_collection"],
#         limit=limit
#     )
    
#     return {"results": results}

# @router.delete("/knowledge-base/{kb_id}", response_model=dict)
# async def delete_knowledge_base(
#     kb_id: uuid_pkg.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Delete a knowledge base and all associated documents"""
#     # Check if knowledge base exists and belongs to user
#     kb = await crud_knowledge_base.get(db=db, id=kb_id)
#     if not kb:
#         raise HTTPException(status_code=404, detail="Knowledge base not found")
        
#     if kb["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not authorized to delete this knowledge base")
    
#     # Delete the knowledge base and associated Qdrant collection
#     success = await document_service.delete_knowledge_base(db=db, kb_id=kb_id)
    
#     return {"success": success}

import io
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import uuid as uuid_pkg

from ...core.db.database import async_get_db
from ...crud.crud_documents import document_service, crud_knowledge_base
from ...schemas.document import KnowledgeBaseRead, DocumentRead, KnowledgeBaseCreate
from ...api.dependencies import get_current_user
from ...models.user import User

logger = logging.getLogger("api-knowledge-base") 
router = APIRouter(tags=["knowledge-base"])


@router.post("/knowledge-base", response_model=KnowledgeBaseRead)
async def create_knowledge_base(
    kb_create: KnowledgeBaseCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new knowledge base"""
    kb = await document_service.create_knowledge_base(
        db=db,
        name=kb_create.name,
        description=kb_create.description,
        owner_id=current_user["id"] 
    )
    return kb

@router.get("/knowledge-base", response_model=List[KnowledgeBaseRead])
async def list_knowledge_bases(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """List all knowledge bases for the current user"""
    kbs = await document_service.get_knowledge_bases_by_owner(
        db=db, owner_id=current_user["id"]
    )
    return kbs

@router.get("/knowledge-base/{kb_id}", response_model=KnowledgeBaseRead)
async def get_knowledge_base_by_id(
    kb_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single knowledge base by its ID."""
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
        
    return kb

@router.post("/knowledge-base/{kb_id}/upload", response_model=DocumentRead)
async def upload_document(
    kb_id: uuid_pkg.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a document for a knowledge base"""
    file_size = 0
    chunk_size = 1024 * 1024
    content = b''
    
    while chunk := await file.read(chunk_size):
        content += chunk
        file_size += len(chunk)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413, 
                detail="File too large. Maximum size is 50MB."
            )
    
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    # FIX: Changed kb.owner_id to kb["owner_id"]
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
    file_obj = io.BytesIO(content)
    
    from ...services.document_processor import document_processor
    try:
        document = await document_processor.process_file(
            db=db,
            file=file_obj,
            filename=file.filename,
            knowledge_base_id=kb_id
        )
        return document
    except Exception as e:
        logger.exception(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
    
@router.get("/knowledge-base/{kb_id}/documents", response_model=List[DocumentRead])
async def list_documents(
    kb_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents in a knowledge base"""
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    # FIX: Changed kb.owner_id to kb["owner_id"]
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
    documents = await document_service.get_documents_by_knowledge_base(
        db=db, kb_id=kb_id
    )
    
    return documents

@router.get("/knowledge-base/{kb_id}/query")
async def query_knowledge_base(
    kb_id: uuid_pkg.UUID,
    q: str,
    limit: int = 5,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Query a knowledge base with vector search"""
    from ...services.vector_search import vector_search
    
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    # FIX: Changed kb.owner_id to kb["owner_id"]
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
    
    # FIX: Changed kb.qdrant_collection to kb["qdrant_collection"]
    results = await vector_search.query(
        query_text=q,
        collection_name=kb["qdrant_collection"],
        limit=limit
    )
    
    return {"results": results}

@router.delete("/knowledge-base/{kb_id}", response_model=dict)
async def delete_knowledge_base(
    kb_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a knowledge base and all associated documents"""
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    # FIX: Changed kb.owner_id to kb["owner_id"]
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this knowledge base")
    
    success = await document_service.delete_knowledge_base(db=db, kb_id=kb_id)
    
    return {"success": success}

@router.delete("/knowledge-base/{kb_id}/documents/{doc_id}", response_model=dict)
async def delete_document(
    kb_id: uuid_pkg.UUID,
    doc_id: uuid_pkg.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific document from a knowledge base"""
    kb = await crud_knowledge_base.get(db=db, id=kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    # FIX: Changed kb.owner_id to kb["owner_id"]
    if kb["owner_id"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")

    success = await document_service.delete_document(db=db, kb_id=kb_id, doc_id=doc_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found in the specified knowledge base")

    return {"success": True, "detail": "Document deleted successfully"}