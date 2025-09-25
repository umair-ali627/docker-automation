# import uuid
# from fastcrud import FastCRUD
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Optional, Dict, Any
# from datetime import datetime, timezone

# from ..models.sip import SIPTrunk, SIPAgentMapping, SIPCall, SIPCallDirection, SIPCallStatus
# from ..schemas.sip import (
#     SIPTrunkCreateInternal,
#     SIPTrunkDelete,
#     SIPTrunkRead,
#     SIPTrunkUpdate,
#     SIPTrunkUpdateInternal,
#     SIPAgentMappingCreateInternal,
#     SIPAgentMappingDelete,
#     SIPAgentMappingRead,
#     SIPAgentMappingUpdate,
#     SIPAgentMappingUpdateInternal,
#     SIPCallCreateInternal,
#     SIPCallRead,
#     SIPCallUpdate,
#     SIPCallUpdateInternal,
#     SIPCallDelete
# )

# # Define FastCRUD for SIP Trunks
# class CRUDSIPTrunkExtended(FastCRUD[
#     SIPTrunk,
#     SIPTrunkCreateInternal,
#     SIPTrunkUpdate,
#     SIPTrunkUpdateInternal,
#     SIPTrunkDelete,
#     SIPTrunkRead
# ]):
#     async def get_by_owner_id(self, db: AsyncSession, *, owner_id: uuid.UUID) -> List[SIPTrunkRead]:
#         """Get all trunks by owner ID"""
#         result = await self.get_multi(db=db, owner_id=owner_id)
#         return result["data"]
        
#     async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[SIPTrunkRead]:
#         """Get trunk by phone number"""
#         trunk = await self.get(db=db, phone_number=phone_number)
#         return trunk
        
#     async def get_by_trunk_id(self, db: AsyncSession, *, trunk_id: str) -> Optional[SIPTrunkRead]:
#         """Get trunk by LiveKit trunk ID"""
#         trunk = await self.get(db=db, trunk_id=trunk_id)
#         return trunk


# # Define FastCRUD for SIP Agent Mappings
# class CRUDSIPAgentMappingExtended(FastCRUD[
#     SIPAgentMapping,
#     SIPAgentMappingCreateInternal,
#     SIPAgentMappingUpdate,
#     SIPAgentMappingUpdateInternal,
#     SIPAgentMappingDelete,
#     SIPAgentMappingRead
# ]):
  
#     async def get_by_inbound_agent_id(self, db: AsyncSession, *, agent_id: uuid.UUID) -> List[SIPAgentMappingRead]:
#         """Get all mappings by inbound agent ID"""
#         result = await self.get_multi(db=db, inbound_agent_id=agent_id)
#         return result["data"]
        
#     async def get_by_outbound_agent_id(self, db: AsyncSession, *, agent_id: uuid.UUID) -> List[SIPAgentMappingRead]:
#         """Get all mappings by outbound agent ID"""
#         result = await self.get_multi(db=db, outbound_agent_id=agent_id)
#         return result["data"]
        
#     async def get_by_trunk_id(self, db: AsyncSession, *, trunk_id: uuid.UUID) -> List[SIPAgentMappingRead]:
#         """Get all mappings by trunk ID"""
#         result = await self.get_multi(db=db, sip_trunk_id=trunk_id)
#         return result["data"]
    
#     async def get_by_dispatch_rule_id(self, db: AsyncSession, *, rule_id: str) -> Optional[SIPAgentMappingRead]:
#         """Get mapping by dispatch rule ID"""
#         mapping = await self.get(db=db, dispatch_rule_id=rule_id)
#         return mapping

# class CRUDSIPCallExtended(FastCRUD[
#     SIPCall,
#     SIPCallCreateInternal,
#     SIPCallUpdate,
#     SIPCallUpdateInternal,
#     SIPCallDelete,
#     SIPCallRead
# ]):
#     async def get_by_call_id(self, db: AsyncSession, *, call_id: str) -> Optional[SIPCallRead]:
#         """Get call by LiveKit call ID"""
#         call = await self.get(db=db, call_id=call_id)
#         return call
        
#     async def get_by_room_id(self, db: AsyncSession, *, room_id: uuid.UUID) -> Optional[SIPCallRead]:
#         """Get call by room ID"""
#         call = await self.get(db=db, room_id=room_id)
#         return call
    
#     async def get_active_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> List[SIPCallRead]:
#         """Get all active calls for a phone number"""
#         result = await self.get_multi(
#             db=db, 
#             phone_number=phone_number, 
#             status__in=[
#                 SIPCallStatus.INITIATED.value, 
#                 SIPCallStatus.RINGING.value, 
#                 SIPCallStatus.ACTIVE.value
#             ]
#         )
#         return result["data"]
    
#     async def mark_call_answered(
#         self, 
#         db: AsyncSession, 
#         *, 
#         call_id: str, 
#         agent_id: Optional[uuid.UUID] = None
#     ) -> Optional[SIPCallRead]:
#         """Mark a call as answered"""
#         update_data = {
#             "status": SIPCallStatus.ACTIVE.value,
#             "answered_at": datetime.now(timezone.utc)
#         }
        
#         if agent_id:
#             update_data["agent_id"] = agent_id
            
#         updated = await self.update(
#             db=db,
#             call_id=call_id,
#             object=SIPCallUpdateInternal(**update_data),
#             return_as_model=True,
#             return_columns=["*"],
#             schema_to_select=SIPCallRead
#         )
        
#         return updated
    
#     async def mark_call_completed(
#         self, 
#         db: AsyncSession, 
#         *, 
#         call_id: str,
#         success: bool = True,
#         metadata: Optional[Dict[str, Any]] = None
#     ) -> Optional[SIPCallRead]:
#         """Mark a call as completed"""
#         call = await self.get_by_call_id(db, call_id=call_id)
#         if not call:
#             return None
            
#         # Calculate duration if the call was answered
#         duration_seconds = None
#         if call.answered_at:
#             now = datetime.now(timezone.utc)
#             duration_seconds = int((now - call.answered_at).total_seconds())
        
#         # Combine existing metadata with new metadata
#         combined_metadata = call.metadata or {}
#         if metadata:
#             combined_metadata.update(metadata)
            
#         updated = await self.update(
#             db=db,
#             call_id=call_id,
#             object=SIPCallUpdateInternal(
#                 status=SIPCallStatus.COMPLETED.value,
#                 completed_at=datetime.now(timezone.utc),
#                 duration_seconds=duration_seconds,
#                 success=success,
#                 metadata=combined_metadata
#             ),
#             return_as_model=True,
#             return_columns=["*"],
#             schema_to_select=SIPCallRead
#         )
        
#         return updated
    
#     async def create_call_record(
#         self,
#         db: AsyncSession,
#         *,
#         call_id: str,
#         room_id: uuid.UUID,
#         direction: SIPCallDirection,
#         phone_number: str,
#         trunk_id: Optional[uuid.UUID] = None,
#         agent_id: Optional[uuid.UUID] = None,
#         metadata: Optional[Dict[str, Any]] = None
#     ) -> SIPCallRead:
#         """Create a new SIP call record"""
#         call = await self.create(
#             db=db,
#             object=SIPCallCreateInternal(
#                 call_id=call_id,
#                 room_id=room_id,
#                 direction=direction,
#                 phone_number=phone_number,
#                 trunk_id=trunk_id,
#                 agent_id=agent_id,
#                 metadata=metadata or {},
#                 status=SIPCallStatus.INITIATED
#             )
#         )
        
#         return SIPCallRead.model_validate(call)


# # Create instance
# crud_sip_trunk = CRUDSIPTrunkExtended(SIPTrunk)
# crud_sip_calls = CRUDSIPCallExtended(SIPCall)
# crud_sip_agent_mapping = CRUDSIPAgentMappingExtended(SIPAgentMapping)


import uuid
from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import update

from ..models.sip import SIPTrunk, SIPAgentMapping, SIPCall, SIPCallDirection, SIPCallStatus
from ..schemas.sip import (
    SIPTrunkCreateInternal,
    SIPTrunkDelete,
    SIPTrunkRead,
    SIPTrunkUpdate,
    SIPTrunkUpdateInternal,
    SIPAgentMappingCreateInternal,
    SIPAgentMappingDelete,
    SIPAgentMappingRead,
    SIPAgentMappingUpdate,
    SIPAgentMappingUpdateInternal,
    SIPCallCreateInternal,
    SIPCallRead,
    SIPCallUpdate,
    SIPCallUpdateInternal,
    SIPCallDelete
)

# Define FastCRUD for SIP Trunks
class CRUDSIPTrunkExtended(FastCRUD[
    SIPTrunk,
    SIPTrunkCreateInternal,
    SIPTrunkUpdate,
    SIPTrunkUpdateInternal,
    SIPTrunkDelete,
    SIPTrunkRead
]):
    # async def get_by_owner_id(self, db: AsyncSession, *, owner_id: uuid.UUID) -> List[SIPTrunkRead]:
    #     """Get all trunks by owner ID"""
    #     result = await self.get_multi(db=db, owner_id=owner_id)
    #     return result["data"]
        
    # async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[SIPTrunkRead]:
    #     """Get trunk by phone number"""
    #     trunk = await self.get(db=db, phone_number=phone_number)
    #     return trunk
        
    # async def get_by_trunk_id(self, db: AsyncSession, *, trunk_id: str) -> Optional[SIPTrunkRead]:
    #     """Get trunk by LiveKit trunk ID"""
    #     trunk = await self.get(db=db, trunk_id=trunk_id)
    #     return trunk

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[SIPTrunkRead]:
        """Get a single trunk by ID, excluding soft-deleted trunks."""
        result = await self.get_multi(db=db, id=id, is_deleted=False)
        return result["data"][0] if result["data"] else None

    async def get_by_owner_id(self, db: AsyncSession, *, owner_id: uuid.UUID) -> List[SIPTrunkRead]:
        """Get all trunks by owner ID, excluding soft-deleted trunks."""
        result = await self.get_multi(db=db, owner_id=owner_id, is_deleted=False)
        return result["data"]

    async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[SIPTrunkRead]:
        """Get trunk by phone number, excluding soft-deleted trunks."""
        result = await self.get_multi(db=db, phone_number=phone_number, is_deleted=False)
        return result["data"][0] if result["data"] else None

    async def get_by_trunk_id(self, db: AsyncSession, *, trunk_id: str) -> Optional[SIPTrunkRead]:
        """Get trunk by LiveKit trunk ID, excluding soft-deleted trunks."""
        result = await self.get_multi(db=db, trunk_id=trunk_id, is_deleted=False)
        return result["data"][0] if result["data"] else None

    async def delete(self, db: AsyncSession, id: uuid.UUID) -> None:
        """Soft delete a SIP trunk by setting is_deleted=True."""
        query = update(self.model).where(self.model.id == id, self.model.is_deleted == False).values(is_deleted=True)
        result = await db.execute(query)
        if result.rowcount == 0:
            raise ValueError(f"SIP trunk not found or already deleted: {id}")
        await db.commit()

# Define FastCRUD for SIP Agent Mappings
class CRUDSIPAgentMappingExtended(FastCRUD[
    SIPAgentMapping,
    SIPAgentMappingCreateInternal,
    SIPAgentMappingUpdate,
    SIPAgentMappingUpdateInternal,
    SIPAgentMappingDelete,
    SIPAgentMappingRead
]):
  
    async def get_by_inbound_agent_id(self, db: AsyncSession, *, agent_id: uuid.UUID) -> List[SIPAgentMappingRead]:
        """Get all mappings by inbound agent ID"""
        result = await self.get_multi(db=db, inbound_agent_id=agent_id)
        return result["data"]
        
    async def get_by_outbound_agent_id(self, db: AsyncSession, *, agent_id: uuid.UUID) -> List[SIPAgentMappingRead]:
        """Get all mappings by outbound agent ID"""
        result = await self.get_multi(db=db, outbound_agent_id=agent_id)
        return result["data"]
        
    async def get_by_trunk_id(self, db: AsyncSession, *, trunk_id: uuid.UUID) -> List[SIPAgentMappingRead]:
        """Get all mappings by trunk ID"""
        result = await self.get_multi(db=db, sip_trunk_id=trunk_id)
        return result["data"]
    
    async def get_by_dispatch_rule_id(self, db: AsyncSession, *, rule_id: str) -> Optional[SIPAgentMappingRead]:
        """Get mapping by dispatch rule ID"""
        mapping = await self.get(db=db, dispatch_rule_id=rule_id)
        return mapping


class CRUDSIPCallExtended(FastCRUD[
    SIPCall,
    SIPCallCreateInternal,
    SIPCallUpdate,
    SIPCallUpdateInternal,
    SIPCallDelete,
    SIPCallRead
]):
    async def get_by_call_id(self, db: AsyncSession, *, call_id: str) -> Optional[SIPCallRead]:
        """Get call by LiveKit call ID, excluding soft-deleted calls."""
        call = await self.get(db=db, call_id=call_id, is_deleted=False)
        return call

    async def get_by_room_id(self, db: AsyncSession, *, room_id: str) -> Optional[SIPCallRead]:
        """Get call by room ID, excluding soft-deleted calls."""
        call = await self.get(db=db, room_id=room_id, is_deleted=False)
        return call

    async def get_active_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> List[SIPCallRead]:
        """Get all active calls for a phone number, excluding soft-deleted calls."""
        result = await self.get_multi(
            db=db,
            phone_number=phone_number,
            status__in=[
                SIPCallStatus.INITIATED.value,
                SIPCallStatus.RINGING.value,
                SIPCallStatus.ACTIVE.value
            ],
            is_deleted=False
        )
        return result["data"]

    async def delete(self, db: AsyncSession, id: uuid.UUID) -> None:
        """Soft delete a SIP call by setting is_deleted=True."""
        query = update(self.model).where(self.model.id == id, self.model.is_deleted == False).values(is_deleted=True)
        result = await db.execute(query)
        if result.rowcount == 0:
            raise ValueError(f"SIP call not found or already deleted: {id}")
        await db.commit()
    
    async def mark_call_answered(
        self, 
        db: AsyncSession, 
        *, 
        call_id: str, 
        agent_id: Optional[uuid.UUID] = None
    ) -> Optional[SIPCallRead]:
        """Mark a call as answered"""
        update_data = {
            "status": SIPCallStatus.ACTIVE.value,
            "answered_at": datetime.now(timezone.utc)
        }
        
        if agent_id:
            update_data["agent_id"] = agent_id
            
        updated = await self.update(
            db=db,
            call_id=call_id,
            object=SIPCallUpdateInternal(**update_data),
            return_as_model=True,
            return_columns=["*"],
            schema_to_select=SIPCallRead
        )
        
        return updated
    
    async def mark_call_completed(
        self, 
        db: AsyncSession, 
        *, 
        call_id: str,
        success: bool = True,
        call_metadata: Optional[Dict[str, Any]] = None   # ✅ renamed
    ) -> Optional[SIPCallRead]:
        """Mark a call as completed"""
        call = await self.get_by_call_id(db, call_id=call_id)
        if not call:
            return None
            
        # Calculate duration if the call was answered
        duration_seconds = None
        if call.answered_at:
            now = datetime.now(timezone.utc)
            duration_seconds = int((now - call.answered_at).total_seconds())
        
        # Combine existing call_metadata with new call_metadata
        combined_metadata = call.call_metadata or {}
        if call_metadata:
            combined_metadata.update(call_metadata)
            
        updated = await self.update(
            db=db,
            call_id=call_id,
            object=SIPCallUpdateInternal(
                status=SIPCallStatus.COMPLETED.value,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration_seconds,
                success=success,
                call_metadata=combined_metadata   # ✅ renamed
            ),
            return_as_model=True,
            return_columns=["*"],
            schema_to_select=SIPCallRead
        )
        
        return updated
    
    async def create_call_record(
        self,
        db: AsyncSession,
        *,
        call_id: str,
        room_id: str,
        direction: SIPCallDirection,
        phone_number: str,
        trunk_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        call_metadata: Optional[Dict[str, Any]] = None   # ✅ renamed
    ) -> SIPCallRead:
        """Create a new SIP call record"""
        call = await self.create(
            db=db,
            object=SIPCallCreateInternal(
                call_id=call_id,
                room_id=room_id,
                direction=direction,
                phone_number=phone_number,
                trunk_id=trunk_id,
                agent_id=agent_id,
                call_metadata=call_metadata or {},   # ✅ renamed
                status=SIPCallStatus.INITIATED
            )
        )

        return SIPCallRead.model_validate(call)

        # Convert SQLAlchemy model to dictionary for SIPCallRead validation
        # call_dict = {
        #     "call_id": call.call_id,
        #     "room_id": call.room_id,
        #     "direction": call.direction,
        #     "phone_number": call.phone_number,
        #     "status": call.status,
        #     "trunk_id": call.trunk_id,
        #     "agent_id": call.agent_id,
        #     "call_metadata": call.call_metadata,
        #     "id": call.id,
        #     "created_at": call.created_at,
        #     # Provide explicit None values for optional fields
        #     "answered_at": None,
        #     "completed_at": None,
        #     "duration_seconds": None,
        #     "success": None,
        # }
        
        # return SIPCallRead.model_validate(call_dict)
        
        # # Ensure all fields required by SIPCallRead are present
        # call_dict = call.__dict__.copy()
        # call_dict.setdefault("answered_at", None)
        # call_dict.setdefault("completed_at", None)
        # call_dict.setdefault("duration_seconds", None)
        # call_dict.setdefault("success", None)
        
        # return SIPCallRead.model_validate(call_dict)

# Create instance
crud_sip_trunk = CRUDSIPTrunkExtended(SIPTrunk)
crud_sip_calls = CRUDSIPCallExtended(SIPCall)
crud_sip_agent_mapping = CRUDSIPAgentMappingExtended(SIPAgentMapping)
