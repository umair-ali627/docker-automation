# import uuid
# import logging

# from typing import List
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession

# from ...schemas.sip import (
#     CompleteSIPSetupCreate,
#     CompleteSIPSetupResponse,
#     SIPTrunkRead,
#     SIPTrunkList,
#     SIPAgentMappingUpdate,
#     SIPAgentMappingRead,
#     SIPAgentMappingCreate,
#     SIPAgentMappingCreateInternal
# )
# from ...core.db.database import async_get_db
# from ...services.sip_factory import sip_factory
# from ...crud.crud_sip import crud_sip_trunk, crud_sip_agent_mapping
# from ...crud.crud_agent_profiles import crud_agent_profiles
# from ..dependencies import get_current_user
# from ...models.user import User

# logger = logging.getLogger("api-sip")
# router = APIRouter(tags=["sip-trunk"])


# @router.post("/sip-trunk", response_model=CompleteSIPSetupResponse)
# async def create_complete_sip_setup(
#     setup_in: CompleteSIPSetupCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create a complete SIP setup including:
#     - Inbound trunk
#     - Outbound trunk
#     - Dispatch rule
#     - Agent association (if agent IDs are provided)
    
#     This single API call handles everything needed for SIP integration.
#     """
#     try:
#         # Create the complete SIP setup
#         result = await sip_factory.register_complete_sip_setup(
#             db=db,
#             owner_id=current_user["id"],
#             name=setup_in.name,
#             description=setup_in.description,
#             sip_termination_uri=setup_in.sip_termination_uri,
#             phone_number=setup_in.phone_number,
#             username=setup_in.username,
#             password=setup_in.password,
#             inbound_agent_id=setup_in.inbound_agent_id,   # Updated to use separate agent IDs
#             outbound_agent_id=setup_in.outbound_agent_id, # instead of single agent_profile_id
#             config=setup_in.config
#         )
#         return result
#     except ValueError as e:
#         # More specific error from the service
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Failed to create SIP setup: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to create SIP setup: {str(e)}")


# @router.get("/sip-trunk", response_model=SIPTrunkList)
# async def list_sip_trunks(
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 100,
# ):
#     """
#     List all SIP trunks owned by the current user.
#     """
#     try:
#         trunks = await crud_sip_trunk.get_by_owner_id(db, owner_id=current_user["id"])
#         return {
#             "items": trunks[skip:skip+limit],
#             "total": len(trunks)
#         }
#     except Exception as e:
#         logger.error(f"Error listing SIP trunks: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to list SIP trunks")

# @router.get("/sip-trunk/{trunk_id}", response_model=SIPTrunkRead)
# async def get_sip_trunk(
#     trunk_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Get details of a specific SIP trunk.
#     """
#     trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
#     if not trunk:
#         raise HTTPException(status_code=404, detail="SIP trunk not found")
    
#     # Check if the user has permission to access this trunk
#     if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     return trunk

# @router.delete("/sip-trunk/{trunk_id}", response_model=dict)
# async def delete_sip_trunk(
#     trunk_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Delete a SIP trunk configuration and its LiveKit resources.
#     """
#     try:
#         # await sip_factory.delete_trunk(trunk_id="ST_x2UrthVqugio")
#         # return {"success": True, "message": "SIP trunk deleted successfully"}
#         trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
#         if not trunk:
#             raise HTTPException(status_code=404, detail="SIP trunk not found")
        
#         # Check if the user has permission to delete this trunk
#         if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#             raise HTTPException(status_code=403, detail="Not enough permissions")
        
#         # Delete associated mappings
#         mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk_id)
#         for mapping in mappings:
#             await sip_factory.unassign_trunk_from_agent(db, mapping["id"])
        
#         # Delete LiveKit resources
#         await sip_factory.delete_trunk(trunk["trunk_id"])
        
#         # Delete from database using FastCRUD
#         await crud_sip_trunk.delete(db=db, id=trunk_id)
        
#         return {"success": True, "message": "SIP trunk deleted successfully"}
#     except ValueError as e:
#         # More specific error from the service
#         raise HTTPException(status_code=400, detail=str(e))
#     except HTTPException:
#         # Re-raise HTTP exceptions directly
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting SIP trunk: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete SIP trunk: {str(e)}")
    
# @router.post("/sip-trunk/{trunk_id}/agent-mapping", response_model=SIPAgentMappingRead)
# async def create_sip_agent_mapping(
#     trunk_id: uuid.UUID,
#     mapping_create: SIPAgentMappingCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create a new SIP agent mapping for an existing trunk.
#     """
#     # Check if trunk exists and user has permission
#     trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
#     if not trunk:
#         raise HTTPException(status_code=404, detail="SIP trunk not found")
    
#     if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # Check for existing mapping
#     existing_mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk_id)
#     if existing_mappings:
#         raise HTTPException(
#             status_code=400, 
#             detail="This trunk already has an agent mapping. Use the update endpoint instead."
#         )
    
#     # Get dispatch rule ID from trunk (would need to add this to the trunk model)
#     # For this example, we'll assume it's stored or needs to be created
#     dispatch_rule_id = trunk.get("dispatch_rule_id", "SDR_fyLeBnThGEpH")

#     # Create mapping
#     mapping = await crud_sip_agent_mapping.create(
#         db=db,
#         object=SIPAgentMappingCreateInternal(
#             sip_trunk_id=trunk_id,
#             inbound_agent_id=mapping_create.inbound_agent_id,
#             outbound_agent_id=mapping_create.outbound_agent_id,
#             dispatch_rule_id=dispatch_rule_id
#         )
#     )
    
#     return mapping

# @router.put("/sip-agent-mapping/{trunk_id}", response_model=dict)
# async def update_sip_agent_mapping(
#     trunk_id: uuid.UUID,
#     mapping_update: SIPAgentMappingUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Update an existing SIP agent mapping to change inbound/outbound agents using Trunk ID.
#     """
#     trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
#     if not trunk:
#         raise HTTPException(status_code=404, detail="SIP trunk not found")
    
#     if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     mapping = await crud_sip_agent_mapping.get_by_trunk_id(db=db, trunk_id=trunk_id)
#     if not mapping:
#         raise HTTPException(status_code=404, detail="SIP agent mapping not found")
    
#     # Validate agents if provided
#     if mapping_update.inbound_agent_id:
#         inbound_agent = await crud_agent_profiles.get(db=db, id=mapping_update.inbound_agent_id)
#         if not inbound_agent:
#             raise HTTPException(status_code=404, detail="Inbound agent profile not found")
    
#     if mapping_update.outbound_agent_id:
#         outbound_agent = await crud_agent_profiles.get(db=db, id=mapping_update.outbound_agent_id)
#         if not outbound_agent:
#             raise HTTPException(status_code=404, detail="Outbound agent profile not found")
    
#     await crud_sip_agent_mapping.update(
#         db=db, 
#         id=mapping[0]["id"], 
#         object=mapping_update
#     )
    
#     return {"success": True, "message": "SIP agent mapping updated successfully"}

import os
import uuid
import logging
from ...core.config import settings
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.sip import TwilioUrlUpdateRequest
from ...schemas.sip import (
    CompleteSIPSetupCreate,
    CompleteSIPSetupResponse,
    OutboundCallInfo,
    OutboundCallRequest,
    OutboundCallResponse,
    SIPTrunkRead,
    SIPTrunkList,
    SIPAgentMappingUpdate,
    SIPAgentMappingRead,
    SIPAgentMappingCreate,
    SIPAgentMappingCreateInternal,
    SIPCallEventType,
    SIPCallDirection
)
from ...core.db.database import async_get_db
from ...services.sip_factory import sip_factory
from ...crud.crud_sip import crud_sip_trunk, crud_sip_agent_mapping
from ...crud.crud_agent_profiles import crud_agent_profiles
from ..dependencies import get_current_user
from ...models.user import User
from twilio.rest import Client
from ...models.connections import Connection
from ...models.sip import SIPCall
from sqlalchemy import select
from fastapi import Response
from twilio.twiml.voice_response import VoiceResponse, Dial
from sqlalchemy import update

logger = logging.getLogger("api-sip")
router = APIRouter(tags=["sip-trunk"])

@router.post("/sip-trunk", response_model=CompleteSIPSetupResponse)
@router.post("/sip-trunk", response_model=CompleteSIPSetupResponse)
async def create_complete_sip_setup(
    setup_in: CompleteSIPSetupCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a complete SIP setup including:
    - Inbound trunk
    - Outbound trunk
    - Dispatch rule
    - Agent association (if agent IDs are provided)
    
    This single API call handles everything needed for SIP integration.
    """
    try:
        # Check if already in a transaction (for debugging)
        if db.in_transaction():
            logger.debug("Using existing database transaction")
        else:
            logger.debug("No existing transaction; relying on session scope")

        # Create the complete SIP setup (validation happens inside)
        result = await sip_factory.register_complete_sip_setup(
            db=db,
            owner_id=current_user["id"],
            name=setup_in.name,
            description=setup_in.description,
            sip_termination_uri=setup_in.sip_termination_uri,
            phone_number=setup_in.phone_number,
            username=setup_in.username,
            password=setup_in.password,
            inbound_agent_id=setup_in.inbound_agent_id,
            outbound_agent_id=setup_in.outbound_agent_id,
            config=setup_in.config
        )
        logger.info(f"Successfully created SIP setup for phone number {setup_in.phone_number}")
        return result
    except ValueError as e:
        logger.error(f"Validation failed during SIP setup creation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating SIP setup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create SIP setup: {str(e)}")

@router.get("/sip-trunk", response_model=SIPTrunkList)
async def list_sip_trunks(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all SIP trunks owned by the current user.
    """
    try:
        trunks = await crud_sip_trunk.get_by_owner_id(db, owner_id=current_user["id"])
        return {
            "items": trunks[skip:skip+limit],
            "total": len(trunks)
        }
    except Exception as e:
        logger.error(f"Error listing SIP trunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list SIP trunks")

@router.get("/sip-trunk/{trunk_id}", response_model=SIPTrunkRead)
async def get_sip_trunk(
    trunk_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific SIP trunk.
    """
    trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
    if not trunk:
        raise HTTPException(status_code=404, detail="SIP trunk not found")
    
    # Check if the user has permission to access this trunk
    if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return trunk


@router.delete("/sip-trunk/{trunk_id}", response_model=dict)
async def delete_sip_trunk(
    trunk_id: uuid.UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a SIP trunk configuration, its associated mappings, and calls.
    """
    try:
        trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP trunk not found")
        
        if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Delete associated mappings (physical delete to clean up)
        mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk_id)
        mapping_errors = []
        for mapping in mappings:
            try:
                await sip_factory.unassign_trunk_from_agent(db, mapping["id"])
            except ValueError as e:
                error_msg = f"Failed to unassign mapping {mapping['id']}: {str(e)}"
                logger.warning(error_msg)
                mapping_errors.append(error_msg)
        
        if mapping_errors:
            logger.warning(f"Encountered {len(mapping_errors)} mapping errors for trunk {trunk_id}: {mapping_errors}")
        
        # Delete LiveKit resources
        try:
            await sip_factory.delete_trunk(trunk["trunk_id"])
            logger.info(f"Successfully deleted LiveKit trunk {trunk['trunk_id']} for trunk {trunk_id}")
        except ValueError as e:
            logger.warning(f"Failed to delete LiveKit trunk {trunk['trunk_id']} for trunk {trunk_id}: {str(e)}")
        
        # Soft delete associated sip_calls
        await db.execute(
            update(SIPCall).where(SIPCall.trunk_id == trunk_id, SIPCall.is_deleted == False).values(is_deleted=True)
        )
        await db.commit()
        logger.info(f"Successfully soft-deleted SIP calls for trunk {trunk_id}")
        
        # Soft delete the trunk in the database
        await crud_sip_trunk.delete(db=db, id=trunk_id)
        logger.info(f"Successfully soft-deleted SIP trunk {trunk_id} from database")
        
        return {"success": True, "message": "SIP trunk deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error soft-deleting SIP trunk {trunk_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to soft-delete SIP trunk: {str(e)}")

# @router.delete("/sip-trunk/{trunk_id}", response_model=dict)
# async def delete_sip_trunk(
#     trunk_id: uuid.UUID,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Delete a SIP trunk configuration and its LiveKit resources.
#     """
#     try:
#         trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
#         if not trunk:
#             raise HTTPException(status_code=404, detail="SIP trunk not found")
        
#         # Check if the user has permission to delete this trunk
#         if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
#             raise HTTPException(status_code=403, detail="Not enough permissions")
        
#         # Delete associated mappings
#         mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk_id)
#         for mapping in mappings:
#             try:
#                 await sip_factory.unassign_trunk_from_agent(db, mapping["id"])
#             except ValueError as e:
#                 logger.warning(f"Failed to unassign mapping {mapping['id']} for trunk {trunk_id}: {str(e)}")
#                 continue  # Continue with other mappings and trunk deletion
        
#         # Delete LiveKit resources
#         try:
#             await sip_factory.delete_trunk(trunk["trunk_id"])
#             logger.info(f"Successfully deleted LiveKit trunk {trunk['trunk_id']} for trunk {trunk_id}")
#         except ValueError as e:
#             logger.warning(f"Failed to delete LiveKit trunk {trunk['trunk_id']} for trunk {trunk_id}: {str(e)}")
#             # Continue with database deletion even if LiveKit resource is missing
        
#         # Delete from database using FastCRUD
#         await crud_sip_trunk.delete(db=db, id=trunk_id)
#         logger.info(f"Successfully deleted SIP trunk {trunk_id} from database")
        
#         return {"success": True, "message": "SIP trunk deleted successfully"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting SIP trunk {trunk_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete SIP trunk: {str(e)}")
    
@router.post("/sip-trunk/{trunk_id}/agent-mapping", response_model=SIPAgentMappingRead)
async def create_sip_agent_mapping(
    trunk_id: uuid.UUID,
    mapping_create: SIPAgentMappingCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new SIP agent mapping for an existing trunk.
    """
    # Check if trunk exists and user has permission
    trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
    if not trunk:
        raise HTTPException(status_code=404, detail="SIP trunk not found")
    
    if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check for existing mapping
    existing_mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk_id)
    if existing_mappings:
        raise HTTPException(
            status_code=400, 
            detail="This trunk already has an agent mapping. Use the update endpoint instead."
        )
    
    # Get dispatch rule ID from trunk (would need to add this to the trunk model)
    # For this example, we'll assume it's stored or needs to be created
    dispatch_rule_id = trunk.get("dispatch_rule_id", "SDR_fyLeBnThGEpH")

    # Create mapping
    mapping = await crud_sip_agent_mapping.create(
        db=db,
        object=SIPAgentMappingCreateInternal(
            sip_trunk_id=trunk_id,
            inbound_agent_id=mapping_create.inbound_agent_id,
            outbound_agent_id=mapping_create.outbound_agent_id,
            dispatch_rule_id=dispatch_rule_id
        )
    )
    
    return mapping

@router.put("/sip-agent-mapping/{trunk_id}", response_model=dict)
async def update_sip_agent_mapping(
    trunk_id: uuid.UUID,
    mapping_update: SIPAgentMappingUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing SIP agent mapping to change inbound/outbound agents using Trunk ID.
    """
    trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
    if not trunk:
        raise HTTPException(status_code=404, detail="SIP trunk not found")
    
    if trunk["owner_id"] != current_user["id"] and not current_user["is_superuser"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    mapping = await crud_sip_agent_mapping.get_by_trunk_id(db=db, trunk_id=trunk_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="SIP agent mapping not found")
    
    # Validate agents if provided
    if mapping_update.inbound_agent_id:
        inbound_agent = await crud_agent_profiles.get(db=db, id=mapping_update.inbound_agent_id)
        if not inbound_agent:
            raise HTTPException(status_code=404, detail="Inbound agent profile not found")
    
    if mapping_update.outbound_agent_id:
        outbound_agent = await crud_agent_profiles.get(db=db, id=mapping_update.outbound_agent_id)
        if not outbound_agent:
            raise HTTPException(status_code=404, detail="Outbound agent profile not found")
    
    await crud_sip_agent_mapping.update(
        db=db, 
        id=mapping[0]["id"], 
        object=mapping_update
    )
    
    return {"success": True, "message": "SIP agent mapping updated successfully"}

# NEW ENDPOINT FOR TWILIO
@router.post("/sip/inbound")
async def handle_inbound_sip(
    request: Request,
    db: AsyncSession = Depends(async_get_db)
):
    """
    Handles an inbound SIP call from a service like Twilio.
    
    This endpoint processes the incoming webhook, finds the relevant
    SIP trunk and agent, creates a call record, and returns TwiML
    to route the call to LiveKit.
    """
    try:
        # Get the form data from the request
        form_data = await request.form()
        logger.info(f"[CALL_START] Incoming call data: {dict(form_data)}")

        to_number = form_data.get('To', '')
        from_number = form_data.get('From', '')
        call_sid = form_data.get('CallSid', '')
        
        logger.info(f"Incoming call from {from_number} to {to_number} with CallSid: {call_sid}")

        twiml_response_data = await sip_factory.handle_inbound_call(
            db=db,
            to_number=to_number,
            from_number=from_number,
            call_sid=call_sid,
            call_direction=SIPCallDirection.INBOUND
        )
        logger.info(f"TwiML response data in handle inbound call: {twiml_response_data}")
        logger.info(f"TwiML response data: {twiml_response_data['sip_host']}")

        room_id = twiml_response_data['room_id']
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Dial>
                <Sip>
                    sip:{to_number}@{twiml_response_data['sip_host']}
                </Sip>
            </Dial>
        </Response>"""

        #         <Response>
        #     <Dial>
        #         <Sip>
        #             sip:{to_number}@{twiml_response_data['sip_host']}
        #             <Header name="X-Call-Sid" value="{call_sid}"/>
        #         </Sip>
        #     </Dial>
        # </Response>"""   
        
        logger.info(f"TwiML response generated for call to {to_number}: {twiml}")

        return Response(content=twiml.strip(), media_type="application/xml")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling inbound SIP call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/livekit/webhook")
async def handle_livekit_webhook(request: Request, db: AsyncSession = Depends(async_get_db)):
    """
    Handle LiveKit webhook events (e.g., participant_joined, room_finished) to update room_id in database.
    """
    payload = await request.json()
    logger.info(f"Received LiveKit webhook: {payload}")

    if payload.get("event") == "participant_joined":
        room_name = payload.get("room", {}).get("name")
        participant = payload.get("participant", {})
        attributes = participant.get("attributes", {})
        from_number = attributes.get("sip.phoneNumber")

        if room_name and from_number:
            # Filter by from_number and select the latest connection
            result = await db.execute(
                select(Connection)
                .where(Connection.room_id.like(f"call-_{from_number}_%"))
                .order_by(Connection.created_at.desc())  # Latest by created_at
                .limit(1)
            )
            connection = result.scalars().first()

            if connection:
                if connection.room_id != room_name:
                    old_room_id = connection.room_id
                    # Update room_id (handle primary key constraint if needed)
                    connection.room_id = room_name
                    await db.commit()
                    logger.info(f"Updated connection room_id from {old_room_id} to {room_name} for CallSid {connection.call_id}")

                    # Update SIP call record
                    call_result = await db.execute(
                        select(SIPCall).where(SIPCall.call_id == connection.call_id)
                    )
                    call_record = call_result.scalar_one_or_none()
                    if call_record:
                        call_record.room_id = room_name
                        await db.commit()
                        logger.info(f"Updated SIPCall room_id to {room_name} for CallSid {connection.call_id}")
                else:
                    logger.info(f"Room_id already matches {room_name} for CallSid {connection.call_id}")
            else:
                logger.warning(f"No connection found for from_number {from_number}")

    elif payload.get("event") == "room_finished":
        room_name = payload.get("room", {}).get("name")
        if room_name:
            # No action (leave connection intact)
            logger.info(f"Room {room_name} finished, connection left intact")

    return Response(status_code=200)

@router.post("/outbound-call", response_model=OutboundCallResponse)
async def create_outbound_call(
    request: OutboundCallRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate outbound SIP calls to one or more phone numbers.

    This endpoint will:
    1. Create a new room for each call.
    2. Associate the agent with the room.
    3. Initiate the SIP call to the specified number.
    4. Track the call in the database.

    Superusers can initiate outbound calls.
    """
    try:
        # NOTE: The check for `current_user["is_superuser"]` is missing here.
        # You should add this check if you want to restrict outbound calls to superusers.

        calls = []
        errors = {}

        # Process each phone number in the request
        for phone_number in request.phone_numbers:
            try:
                # Call the sip_factory to create the outbound call
                room_id, call_id, sip_participant_info = await sip_factory.create_outbound_call(
                    db=db,
                    phone_number=phone_number,
                    agent_id=request.agent_id,
                    trunk_id=request.trunk_id,
                    attributes=request.attributes
                )

                # Log the extra object for debugging
                logger.info(
                    f"Call to {phone_number} dispatched. "
                    f"Agent Job ID: {call_id}, "
                    f"SIP Call ID: {sip_participant_info.sip_call_id}"
                )
                calls.append(OutboundCallInfo(
                    phone_number=phone_number,
                    # call_id=call_id,
                    call_id=sip_participant_info.sip_call_id,
                    room_id=room_id
                ))
            except Exception as e:
                errors[phone_number] = str(e)

        return OutboundCallResponse(
            success=len(calls) > 0,
            calls=calls,
            errors=errors
        )
    except Exception as e:
        logger.error(f"Failed to initiate outbound calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate outbound calls: {str(e)}"
        )

@router.get("/call/{call_id}")
async def get_call_status(
    call_id: str,
    db: AsyncSession = Depends(async_get_db)
):
    """
    Get status information for a SIP call by its LiveKit SIP call ID.
    """
    status = await sip_factory.get_outbound_call_status(db=db, call_id=call_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Call with ID {call_id} not found")
    return status


@router.post("/twilio/update-url")
async def update_twilio_url(
    request: TwilioUrlUpdateRequest
):
    """
    Endpoint to update Twilio phone number voice URL configuration.
    """
    try:
        logger.info(f"[TWILIO_UPDATE_URL] Updating voice URL for phone number: {request.phone_number}")

        # Initialize Twilio client using environment variables
        # Ensure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set in your environment
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # auth_token = os.getenv('TWILIO_AUTH_TOKEN')

        logger.info(f"HERE TWILIO KEYS: {account_sid}, {auth_token}")
        
        # if not account_sid or not auth_token:
        #     raise HTTPException(
        #         status_code=500,
        #         detail="Twilio credentials not found in environment variables."
        #     )
            
        twilio_client = Client(account_sid, auth_token)

        # Fetch phone number by its value
        phone_numbers = twilio_client.incoming_phone_numbers.list(phone_number=request.phone_number)

        if not phone_numbers:
            raise HTTPException(
                status_code=404,
                detail=f"Phone number {request.phone_number} not found in Twilio account"
            )

        # Get the first matching phone number's SID
        phone_number_sid = phone_numbers[0].sid

        # Update the phone number configuration
        updated_number = twilio_client \
            .incoming_phone_numbers(phone_number_sid) \
            .update(voice_url=request.url)
        

        return {
            "status": "success",
            "phone_number": updated_number.phone_number,
            "friendly_name": updated_number.friendly_name,
            "voice_url": updated_number.voice_url
        }

    except Exception as e:
        logger.error(f"[TWILIO_UPDATE_URL_ERROR] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))