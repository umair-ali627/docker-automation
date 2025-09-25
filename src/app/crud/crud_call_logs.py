import uuid
import json
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.exceptions import ClientError
from fastcrud import FastCRUD

from ..core.config import settings
from ..models.call_logs import CallLog
from ..models.agent_profile import AgentProfile
from ..schemas.call_logs import (
    CallLogCreate,
    CallLogUpdate,
    CallLogRead,
    CallLogCreateInternal,
    CallLogUpdateInternal,
    CallLogDelete
)

# --- S3 Helper Function ---
s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

async def upload_conversation_to_s3(conversation_data: List[dict], owner_id: uuid.UUID) -> str:
    """Uploads conversation JSON to S3 and returns the object URL."""
    if not settings.S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")

    conversation_json = json.dumps(conversation_data, indent=2)
    file_key = f"conversations/{owner_id}/{uuid.uuid4()}.json"

    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=file_key,
            Body=conversation_json,
            ContentType="application/json",
        )
        url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
        return url
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload conversation log.")

class CRUDCallLog(FastCRUD[CallLog, CallLogCreateInternal, CallLogUpdate, CallLogUpdateInternal, CallLogDelete, CallLogRead]):
    
    async def create_log(self, db: AsyncSession, *, obj_in: CallLogCreate) -> CallLog:
        """
        Creates a new call log, determines the owner from the agent_id,
        and uploads the conversation transcript to S3.
        """
        agent_stmt = select(AgentProfile).where(AgentProfile.id == obj_in.agent_id)
        agent_result = await db.execute(agent_stmt)
        agent_profile = agent_result.scalar_one_or_none()
        
        if not agent_profile:
            raise HTTPException(status_code=404, detail=f"Agent with id {obj_in.agent_id} not found.")

        owner_id = agent_profile.owner_id
        conversation_url = None
        if obj_in.conversation:
            conversation_url = await upload_conversation_to_s3(obj_in.conversation, owner_id)
        
        create_data = obj_in.model_dump(exclude={"conversation"})
        create_data["owner_id"] = owner_id
        create_data["conversation_url"] = conversation_url
        
        internal_obj = CallLogCreateInternal(**create_data)
        return await super().create(db=db, object=internal_obj)

    async def get_log(self, db: AsyncSession, *, id: uuid.UUID, owner_id: uuid.UUID) -> Optional[CallLog]:
        """Gets a single non-deleted call log, ensuring it belongs to the owner."""
        stmt = select(self.model).where(
            self.model.id == id, 
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: uuid.UUID, skip: int = 0, limit: int = 100, room_name: Optional[str] = None
    ) -> List[CallLog]:
        """Gets all non-deleted call logs for a specific owner."""
        query = select(self.model).where(
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        )
        if room_name:
            query = query.where(self.model.room_name.ilike(f"%{room_name}%"))
        query = query.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_by_owner(self, db: AsyncSession, *, owner_id: uuid.UUID, room_name: Optional[str] = None) -> int:
        """Counts all non-deleted call logs for a specific owner."""
        query = select(func.count()).select_from(self.model).where(
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        )
        if room_name:
            query = query.where(self.model.room_name.ilike(f"%{room_name}%"))
        result = await db.execute(query)
        return result.scalar_one()
  
    async def get_multi_by_agent(
        self, db: AsyncSession, *, owner_id: uuid.UUID, agent_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[CallLog]:
        """Gets all call logs for a specific agent, ensuring ownership."""
        query = select(self.model).where(
            and_(
                self.model.owner_id == owner_id,
                self.model.agent_id == agent_id,
                self.model.is_deleted == False  # <-- Filter added
            )
        ).offset(skip).limit(limit).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def count_by_agent(self, db: AsyncSession, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> int:
        """Counts all non-deleted call logs for a specific agent, ensuring ownership."""
        query = select(func.count()).select_from(self.model).where(
            and_(
                self.model.owner_id == owner_id,
                self.model.agent_id == agent_id,
                self.model.is_deleted == False  # <-- Filter added
            )
        )
        result = await db.execute(query)
        return result.scalar_one()
        
    async def update_log(
        self, db: AsyncSession, *, id: uuid.UUID, obj_in: CallLogUpdate, owner_id: uuid.UUID
    ) -> Optional[CallLog]:
        """Updates a call log, handling conversation re-upload if necessary."""
        stmt = select(self.model).where(
            self.model.id == id, 
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        
        if "conversation" in update_data:
            conversation_url = await upload_conversation_to_s3(update_data.pop("conversation"), owner_id)
            update_data["conversation_url"] = conversation_url

        await super().update(db=db, object=update_data, id=id, owner_id=owner_id)
        
        await db.refresh(db_obj)
        
        return db_obj

    async def delete_log(self, db: AsyncSession, *, id: uuid.UUID, owner_id: uuid.UUID) -> Optional[CallLog]:
        """
        Soft deletes a call log by setting its 'is_deleted' flag to True.
        """
        stmt = select(self.model).where(
            self.model.id == id, 
            self.model.owner_id == owner_id
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if not db_obj:
            return None

        db_obj.is_deleted = True
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

crud_call_logs = CRUDCallLog(CallLog)