# import logging
# import uuid
# from typing import Dict, Any, Optional, List

# from livekit import api
# from livekit.protocol.sip import (
#     SIPInboundTrunkInfo, 
#     SIPOutboundTrunkInfo, 
#     SIPTransport,
#     SIPDispatchRule,
#     SIPHeaderOptions,
#     SIPMediaEncryption,
#     SIPDispatchRuleIndividual
# )
# from sqlalchemy.ext.asyncio import AsyncSession

# from ..core.config import settings
# from ..schemas.agent_reference import AgentReferenceLookupCreateInternal
# from ..schemas.sip import (
#     CompleteSIPSetupResponse,
#     SIPTrunkCreateInternal,
#     SIPTrunkRead,
#     SIPAgentMappingCreateInternal,
#     SIPAgentMappingRead
# )
# from ..crud.crud_sip import crud_sip_trunk, crud_sip_agent_mapping
# from ..crud.crud_agent_profiles import crud_agent_profiles
# from ..crud.crud_agent_reference import crud_agent_references

# logger = logging.getLogger("sip-factory")

# class SIPFactory:
#     def __init__(self):
#         self.livekit_url = settings.LIVEKIT_HOST
#         self.api_key = settings.LIVEKIT_API_KEY
#         self.api_secret = settings.LIVEKIT_API_SECRET
        
#         # Initialize LiveKit API client lazily
#         self.lk_api = None
    
#     async def _get_api(self) -> api.LiveKitAPI:
#         """Get or initialize the LiveKit API client"""
#         if self.lk_api is None:

#             # Make sure the LiveKit URL is properly formatted
#             livekit_url = self.livekit_url
#             logger.info(f"livekit_url heree: {livekit_url}")
#             # if not livekit_url.startswith(("http://", "https://")):
#             #     livekit_url = f"https://{livekit_url}"
#             #     logger.info(f"formatted livekit_url heree: {livekit_url}")

#             # Normalize URL for WebSocket
#             if not livekit_url.startswith(("http://", "https://", "ws://", "wss://")):
#                 livekit_url = f"wss://{livekit_url}"
#                 logger.info(f"Normalized LiveKit URL (added wss://): {livekit_url}")
#             elif livekit_url.startswith("https://"):
#                 livekit_url = livekit_url.replace("https://", "wss://")
#                 logger.info(f"Normalized LiveKit URL (https:// to wss://): {livekit_url}")
#             elif livekit_url.startswith("http://"):
#                 livekit_url = livekit_url.replace("http://", "ws://")
#                 logger.info(f"Normalized LiveKit URL (http:// to ws://): {livekit_url}")
#             else:
#                 logger.info(f"LiveKit URL already in correct format: {livekit_url}")

#             self.lk_api = api.LiveKitAPI(
#                 url=livekit_url,
#                 api_key=self.api_key,
#                 api_secret=self.api_secret,
#             )
        
#         return self.lk_api
    
#     async def aclose(self):
#         """Close the LiveKit API client"""
#         if self.lk_api:
#             await self.lk_api.aclose()
#             self.lk_api = None
    
#     async def create_inbound_trunk(
#         self, 
#         name: str,
#         phone_number: str,
#         username: Optional[str] = None,
#         password: Optional[str] = None
#     ) -> SIPInboundTrunkInfo:
#         """Create an inbound SIP trunk in LiveKit"""
#         try:
#             lk_api = await self._get_api()
            
#             # Create the inbound trunk with minimal configuration
#             trunk = SIPInboundTrunkInfo(
#                 name=name,
#                 numbers=[phone_number]
#             )
            
#             # Add authentication only if provided
#             if username and password:
#                 trunk.auth_username = username
#                 trunk.auth_password = password
            
#             # Call LiveKit API to create the trunk
#             create_request = api.CreateSIPInboundTrunkRequest(trunk=trunk)
#             logger.info(f"Sending create inbound trunk request: {create_request}")
#             response = await lk_api.sip.create_sip_inbound_trunk(create_request)
#             logger.info(f"Inbound trunk created: {response.sip_trunk_id}")
            
#             logger.info(f"Created inbound SIP trunk: {response.sip_trunk_id}")
#             return response
#         except Exception as e:
#             logger.error(f"Error creating inbound SIP trunk: {str(e)}")
#             raise ValueError(f"Failed to create inbound SIP trunk: {str(e)}")
    
#     # async def create_inbound_trunk(
#     #     self, 
#     #     name: str,
#     #     address: str,
#     #     phone_number: str,
#     #     username: Optional[str] = None,
#     #     password: Optional[str] = None
#     # ) -> SIPInboundTrunkInfo:
#     #     """Create an inbound SIP trunk in LiveKit"""
#     #     try:
#     #         lk_api = await self._get_api()
            
#     #         # Create the inbound trunk with minimal configuration
#     #         trunk = SIPInboundTrunkInfo(
#     #             name=name,
#     #             numbers=[phone_number],
#     #             # allowed_addresses=[address],
#     #             # include_headers=SIPHeaderOptions.SIP_X_HEADERS,
#     #             # media_encryption=SIPMediaEncryption.SIP_MEDIA_ENCRYPT_ALLOW
#     #         )
            
#     #         # Add authentication only if provided
#     #         if username and password:
#     #             trunk.auth_username = username
#     #             trunk.auth_password = password
            
#     #         # Call LiveKit API to create the trunk
#     #         create_request = api.CreateSIPInboundTrunkRequest(trunk=trunk)
#     #         response = await lk_api.sip.create_sip_inbound_trunk(create_request)
            
#     #         logger.info(f"Created inbound SIP trunk: {response.sip_trunk_id}")
#     #         return response
#     #     except Exception as e:
#     #         logger.error(f"Error creating inbound SIP trunk: {str(e)}")
#     #         raise ValueError(f"Failed to create inbound SIP trunk: {str(e)}")
    
#     async def create_outbound_trunk(
#         self,
#         name: str,
#         address: str,
#         username: str,
#         password: str,
#         phone_number: str
#     ) -> SIPOutboundTrunkInfo:
#         """Create an outbound SIP trunk in LiveKit"""
#         try:
#             lk_api = await self._get_api()
            
#             # Create the outbound trunk
#             trunk = SIPOutboundTrunkInfo(
#                 name=name,
#                 address=address,
#                 transport=SIPTransport.SIP_TRANSPORT_UDP,
#                 numbers=[phone_number],
#                 auth_username=username,
#                 auth_password=password,
#                 include_headers=SIPHeaderOptions.SIP_X_HEADERS,
#                 media_encryption=SIPMediaEncryption.SIP_MEDIA_ENCRYPT_ALLOW
#             )
            
#             # Call LiveKit API to create the trunk
#             create_request = api.CreateSIPOutboundTrunkRequest(trunk=trunk)
#             response = await lk_api.sip.create_sip_outbound_trunk(create_request)
            
#             logger.info(f"Created outbound SIP trunk: {response.sip_trunk_id}")
#             return response
#         except Exception as e:
#             logger.error(f"Error creating outbound SIP trunk: {str(e)}")
#             raise ValueError(f"Failed to create outbound SIP trunk: {str(e)}")
    
#     async def create_dispatch_rule(
#         self,
#         trunk_id: str,
#         room_name: str,
#         phone_number: str,
#         name: str,
#     ) -> str:
#         """Create a SIP dispatch rule in LiveKit"""
#         try:
#             lk_api = await self._get_api()
            
#             # Create the dispatch rule
#             rule = SIPDispatchRule(
#                 dispatch_rule_individual=SIPDispatchRuleIndividual(
#                     room_prefix="call",
#                 )
#             )
            
#             # Call LiveKit API to create the dispatch rule
#             create_request = api.CreateSIPDispatchRuleRequest(
#                 rule=rule,
#                 trunk_ids=[trunk_id],
                
#                 # inbound_numbers=[phone_number],
#                 name=name
#             )
            
#             response = await lk_api.sip.create_sip_dispatch_rule(create_request)
            
#             logger.info(f"Created SIP dispatch rule: {response.sip_dispatch_rule_id}")
#             return response.sip_dispatch_rule_id
#         except Exception as e:
#             logger.error(f"Error creating dispatch rule: {str(e)}")
#             raise ValueError(f"Failed to create dispatch rule: {str(e)}")
    
#     async def delete_trunk(self, trunk_id: str) -> None:
#         """Delete a SIP trunk from LiveKit"""
#         try:
#             lk_api = await self._get_api()
            
#             # Call LiveKit API to delete the trunk
#             delete_request = api.DeleteSIPTrunkRequest(sip_trunk_id=trunk_id)
#             await lk_api.sip.delete_sip_trunk(delete_request)
            
#             logger.info(f"Deleted SIP trunk: {trunk_id}")
#         except Exception as e:
#             logger.error(f"Error deleting SIP trunk: {str(e)}")
#             raise ValueError(f"Failed to delete SIP trunk: {str(e)}")
    
#     async def delete_dispatch_rule(self, rule_id: str) -> None:
#         """Delete a SIP dispatch rule from LiveKit"""
#         try:
#             lk_api = await self._get_api()
            
#             # Call LiveKit API to delete the dispatch rule
#             delete_request = api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule_id)
#             await lk_api.sip.delete_sip_dispatch_rule(delete_request)
            
#             logger.info(f"Deleted SIP dispatch rule: {rule_id}")
#         except Exception as e:
#             logger.error(f"Error deleting dispatch rule: {str(e)}")
#             raise ValueError(f"Failed to delete dispatch rule: {str(e)}")
    
#     async def unassign_trunk_from_agent(
#         self,
#         db: AsyncSession,
#         mapping_id: uuid.UUID
#     ) -> None:
#         """Remove a SIP trunk assignment from an agent profile"""
#         try:
#             # Retrieve the mapping
#             mapping = await crud_sip_agent_mapping.get(db=db, id=mapping_id)
#             if not mapping:
#                 raise ValueError(f"SIP agent mapping not found: {mapping_id}")

#             # Use dictionary access instead of attribute access
#             if mapping.get("dispatch_rule_id"):  # Change mapping.dispatch_rule_id to mapping.get("dispatch_rule_id")
#                 await self.delete_dispatch_rule(mapping["dispatch_rule_id"])  # Or mapping.get("dispatch_rule_id")
                  
#             # Delete the mapping from the database using FastCRUD
#             await crud_sip_agent_mapping.delete(db=db, id=mapping_id)
            
#             logger.info(f"Unassigned trunk from agent: {mapping_id}")
#         except Exception as e:
#             logger.error(f"Error unassigning trunk from agent: {str(e)}")
#             raise ValueError(f"Failed to unassign trunk from agent: {str(e)}")
    
#     async def register_complete_sip_setup(
#         self,
#         db: AsyncSession,
#         owner_id: uuid.UUID,
#         name: str,
#         description: str,
#         sip_termination_uri: str,
#         phone_number: str,
#         username: str,
#         password: str,
#         inbound_agent_id: Optional[uuid.UUID] = None,
#         outbound_agent_id: Optional[uuid.UUID] = None,
#         config: Dict[str, Any] = None
#     ) -> CompleteSIPSetupResponse:
#         """
#         Create a complete SIP setup including:
#         - Inbound trunk
#         - Outbound trunk 
#         - Dispatch rule
#         - Agent association
#         All in one operation with improved error handling
#         """
#         # Keep track of created resources for cleanup if needed
#         created_resources = {
#             "inbound_trunk_id": None,
#             "outbound_trunk_id": None,
#             "dispatch_rule_id": None
#         }
        
#         try:
#             logger.info(f"Starting creation of complete SIP setup for {phone_number}")
            
#             # Create inbound trunk
#             logger.info(f"Creating inbound SIP trunk for {phone_number}")
#             inbound_trunk = await self.create_inbound_trunk(
#                 name=f"{name} (Inbound)",
#                 # address=sip_termination_uri,
#                 phone_number=phone_number
#             )
#             logger.info(f"inbound_trunk: {inbound_trunk}")
#             if not inbound_trunk or not inbound_trunk.sip_trunk_id:
#                 raise ValueError("Failed to create inbound SIP trunk - empty response")
            
#             created_resources["inbound_trunk_id"] = inbound_trunk.sip_trunk_id
#             logger.info(f"Created inbound SIP trunk: {inbound_trunk.sip_trunk_id}")
            
#             # Create outbound trunk
#             logger.info(f"Creating outbound SIP trunk for {phone_number}")
#             outbound_trunk = await self.create_outbound_trunk(
#                 name=f"{name} (Outbound)",
#                 address=sip_termination_uri,
#                 username=username,
#                 password=password,
#                 phone_number=phone_number
#             )
#             if not outbound_trunk or not outbound_trunk.sip_trunk_id:
#                 raise ValueError("Failed to create outbound SIP trunk - empty response")
                
#             created_resources["outbound_trunk_id"] = outbound_trunk.sip_trunk_id
#             logger.info(f"Created outbound SIP trunk: {outbound_trunk.sip_trunk_id}")
            
#             # Save trunks in database
#             inbound_db = await crud_sip_trunk.create(
#                 db=db, 
#                 object=SIPTrunkCreateInternal(
#                     name=f"{name} (Inbound)",
#                     description=description,
#                     trunk_type="inbound",
#                     sip_termination_uri=sip_termination_uri,
#                     phone_number=phone_number,
#                     owner_id=owner_id,
#                     trunk_id=inbound_trunk.sip_trunk_id,
#                     config=config or {}
#                 )
#             )
            
#             outbound_db = await crud_sip_trunk.create(
#                 db=db, 
#                 object=SIPTrunkCreateInternal(
#                     name=f"{name} (Outbound)",
#                     description=description,
#                     trunk_type="outbound",
#                     sip_termination_uri=sip_termination_uri,
#                     username=username,
#                     password=password,
#                     phone_number=phone_number,
#                     owner_id=owner_id,
#                     trunk_id=outbound_trunk.sip_trunk_id,
#                     config=config or {}
#                 )
#             )
            
#             # Generate a unique room UUID for phone number
#             room_uuid = uuid.uuid4()
#             room_name = str(room_uuid)
#             logger.info(f"Generated room UUID {room_uuid} for SIP integration")
            
#             # Create dispatch rule 
#             logger.info(f"Creating SIP dispatch rule for phone number {phone_number}")
#             dispatch_rule_id = await self.create_dispatch_rule(
#                 trunk_id=inbound_trunk.sip_trunk_id,
#                 room_name=room_name,
#                 phone_number=phone_number,
#                 name=f"SIP {phone_number}",
#                 # inbound_agent_id=inbound_agent_id
#             )
#             if not dispatch_rule_id:
#                 raise ValueError("Failed to create SIP dispatch rule - empty response")
                
#             created_resources["dispatch_rule_id"] = dispatch_rule_id
#             logger.info(f"Created SIP dispatch rule: {dispatch_rule_id}")
            
#             # Validate agents if provided (but don't require them)
#             if inbound_agent_id:
#                 inbound_agent = await crud_agent_profiles.get(db=db, id=inbound_agent_id)
#                 if not inbound_agent:
#                     raise ValueError(f"Inbound agent profile with ID {inbound_agent_id} not found")
                
#                 # Create agent reference for room-agent association
#                 logger.info(f"Creating agent reference for room {room_uuid} and inbound agent {inbound_agent_id}")
#                 await crud_agent_references.create(
#                     db=db,
#                     object=AgentReferenceLookupCreateInternal(
#                         roomid=room_uuid,
#                         agentid=inbound_agent_id
#                     )
#                 )
            
#             if outbound_agent_id:
#                 outbound_agent = await crud_agent_profiles.get(db=db, id=outbound_agent_id)
#                 if not outbound_agent:
#                     raise ValueError(f"Outbound agent profile with ID {outbound_agent_id} not found")
            
#             # Always create a mapping record to store the dispatch rule ID
#             mapping_create = SIPAgentMappingCreateInternal(
#                 sip_trunk_id=inbound_db.id,
#                 inbound_agent_id=inbound_agent_id,  # Can be None
#                 outbound_agent_id=outbound_agent_id,  # Can be None
#                 dispatch_rule_id=dispatch_rule_id
#             )
            
#             mapping = await crud_sip_agent_mapping.create(db=db, object=mapping_create)
#             logger.info(f"Created SIP agent mapping with ID {mapping.id} and dispatch rule ID {dispatch_rule_id}")
            
#             logger.info(f"Successfully completed SIP setup for {phone_number}")
            
#             return CompleteSIPSetupResponse(
#                 inbound_trunk=inbound_db,
#                 outbound_trunk=outbound_db,
#                 agent_mapping=mapping,
#                 dispatch_rule_id=dispatch_rule_id
#             )
            
#         except Exception as e:
#             logger.error(f"Error during SIP setup creation: {str(e)}")
            
#             # Perform cleanup of LiveKit resources
#             await self._cleanup_resources(created_resources)
            
#             # Re-raise the exception
#             raise ValueError(f"Failed to create complete SIP setup: {str(e)}")

#     async def _cleanup_resources(self, created_resources: Dict[str, Any]) -> None:
#         """Clean up LiveKit API resources when a transaction fails."""
#         cleanup_errors = []
        
#         # Delete dispatch rule
#         if created_resources["dispatch_rule_id"]:
#             try:
#                 logger.warning(f"Cleaning up dispatch rule: {created_resources['dispatch_rule_id']}")
#                 await self.delete_dispatch_rule(created_resources["dispatch_rule_id"])
#             except Exception as e:
#                 error_msg = f"Failed to delete dispatch rule: {str(e)}"
#                 logger.error(error_msg)
#                 cleanup_errors.append(error_msg)
        
#         # Delete outbound trunk
#         if created_resources["outbound_trunk_id"]:
#             try:
#                 logger.warning(f"Cleaning up outbound trunk: {created_resources['outbound_trunk_id']}")
#                 await self.delete_trunk(created_resources["outbound_trunk_id"])
#             except Exception as e:
#                 error_msg = f"Failed to delete outbound trunk: {str(e)}"
#                 logger.error(error_msg)
#                 cleanup_errors.append(error_msg)
        
#         # Delete inbound trunk
#         if created_resources["inbound_trunk_id"]:
#             try:
#                 logger.warning(f"Cleaning up inbound trunk: {created_resources['inbound_trunk_id']}")
#                 await self.delete_trunk(created_resources["inbound_trunk_id"])
#             except Exception as e:
#                 error_msg = f"Failed to delete inbound trunk: {str(e)}"
#                 logger.error(error_msg)
#                 cleanup_errors.append(error_msg)
        
#         if cleanup_errors:
#             logger.error(f"Encountered {len(cleanup_errors)} errors during cleanup: {', '.join(cleanup_errors)}")
#         else:
#             logger.info("Cleanup completed successfully")

# # Create a singleton instance
# sip_factory = SIPFactory()

import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from ..utils.db_utils import with_worker_db

from livekit import api
from livekit.protocol.sip import (
    SIPInboundTrunkInfo, 
    SIPOutboundTrunkInfo, 
    SIPTransport,
    SIPDispatchRule,
    SIPHeaderOptions,
    SIPMediaEncryption,
    SIPDispatchRuleIndividual,
    SIPParticipantInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..core.config import settings
# from livekit.protocol.agent.job import CreateAgentJobRequest
from ..schemas.agent_reference import AgentReferenceLookupCreateInternal
from ..schemas.sip import (
    CompleteSIPSetupResponse,
    SIPTrunkCreateInternal,
    SIPTrunkRead,
    SIPAgentMappingCreateInternal,
    SIPAgentMappingRead,
    SIPCallDirection
)
from ..crud.crud_sip import crud_sip_trunk, crud_sip_agent_mapping, crud_sip_calls
from ..crud.crud_agent_profiles import crud_agent_profiles
from ..crud.crud_connections import crud_connections
from ..crud.crud_agent_reference import crud_agent_references
import secrets  # Add this import at top of sip_factory.py for secure password generation
# from twirp.errors import TwirpError, NotFound
from livekit.api import TwirpError

logger = logging.getLogger("sip-factory")

class SIPFactory:
    def __init__(self):
        self.livekit_url = settings.LIVEKIT_HOST
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        
        # Initialize LiveKit API client lazily
        self.lk_api = None
    
    async def _get_api(self) -> api.LiveKitAPI:
        """Get or initialize the LiveKit API client"""
        if self.lk_api is None:
            # Normalize URL for WebSocket
            livekit_url = self.livekit_url
            if not livekit_url.startswith(("http://", "https://", "ws://", "wss://")):
                livekit_url = f"wss://{livekit_url}"
            elif livekit_url.startswith("https://"):
                livekit_url = livekit_url.replace("https://", "wss://")
            elif livekit_url.startswith("http://"):
                livekit_url = livekit_url.replace("http://", "ws://")

            self.lk_api = api.LiveKitAPI(
                url=livekit_url,
                api_key=self.api_key,
                api_secret=self.api_secret,
            )
        
        return self.lk_api
    
    async def aclose(self):
        """Close the LiveKit API client"""
        if self.lk_api:
            await self.lk_api.aclose()
            self.lk_api = None
    
    async def create_inbound_trunk(
        self, 
        name: str,
        phone_number: str,
        username: str,
        password: str,
        # username: Optional[str] = None,
        # password: Optional[str] = None
    ) -> SIPInboundTrunkInfo:
        """Create an inbound SIP trunk in LiveKit"""
        try:
            lk_api = await self._get_api()

            logger.info(f"create_inbound_trunk Creating inbound SIP trunk for {phone_number} with username {username} and password {password}")
            
            # Create the inbound trunk with minimal configuration
            # trunk = SIPInboundTrunkInfo(
            # name=name,
            # numbers=[phone_number],
            # krisp_enabled=True,
            # auth_username=username,
            # auth_password=password,
            # allowed_addresses=[
            #     "54.172.60.0/30",      # North America Virginia (primary US)
            #     "54.244.51.0/30",      # North America Oregon (CA/West Coast)
            #     "54.171.127.192/30",   # North America Oregon (additional)
            #     "35.156.191.128/30",   # Europe Frankfurt (fallback)
            #     "54.65.63.192/30"      # Asia-Pacific Tokyo (global backup)
            #     ]
            # )
            trunk = SIPInboundTrunkInfo(
                name=name,
                numbers=[phone_number],
                krisp_enabled=True,
            )
            
            # Add authentication only if provided
            # if username and password:
            #     trunk.auth_username = username
            #     trunk.auth_password = password
            
            # Call LiveKit API to create the trunk
            create_request = api.CreateSIPInboundTrunkRequest(trunk=trunk)
            response = await lk_api.sip.create_sip_inbound_trunk(create_request)

            logger.info(f"Created inbound SIP trunk: {response.sip_trunk_id}")

            return response
        except Exception as e:
            logger.error(f"Error creating inbound SIP trunk: {str(e)}")
            raise ValueError(f"Failed to create inbound SIP trunk: {str(e)}")
    
    async def create_outbound_trunk(
        self,
        name: str,
        address: str,
        username: str,
        password: str,
        phone_number: str
    ) -> SIPOutboundTrunkInfo:
        """Create an outbound SIP trunk in LiveKit"""
        try:
            lk_api = await self._get_api()
            
            # Create the outbound trunk
            trunk = SIPOutboundTrunkInfo(
                name=name,
                address=address,
                transport=SIPTransport.SIP_TRANSPORT_TCP,
                numbers=[phone_number],
                auth_username=username,
                auth_password=password,
                include_headers=SIPHeaderOptions.SIP_X_HEADERS,
                media_encryption=SIPMediaEncryption.SIP_MEDIA_ENCRYPT_DISABLE
                # media_encryption=SIPMediaEncryption.SIP_MEDIA_ENCRYPT_ALLOW
            )
            
            # Call LiveKit API to create the trunk
            create_request = api.CreateSIPOutboundTrunkRequest(trunk=trunk)
            response = await lk_api.sip.create_sip_outbound_trunk(create_request)
            
            return response
        except Exception as e:
            logger.error(f"Error creating outbound SIP trunk: {str(e)}")
            raise ValueError(f"Failed to create outbound SIP trunk: {str(e)}")


    async def create_dispatch_rule(
        self,
        trunk_id: str,
        room_name: str,
        phone_number: str,
        name: str,
        agent_name: Optional[str] = None, # New parameter
        agent_metadata: Optional[str] = None # New parameter
    ) -> str:
        """Create a SIP dispatch rule in LiveKit"""
        try:
            lk_api = await self._get_api()
            
            # Create the dispatch rule
            rule = SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix="call-",
                )
            )

            # Create the RoomConfiguration with agent details if provided
            room_config = None
            room_config = api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(
                    agent_name="convoi-telephone-agent",
                    metadata=""
                )]
            )
            
            # Call LiveKit API to create the dispatch rule
            create_request = api.CreateSIPDispatchRuleRequest(
                rule=rule,
                trunk_ids=[trunk_id],
                name=name,
                room_config=room_config,
            )
            
            response = await lk_api.sip.create_sip_dispatch_rule(create_request)
            
            return response.sip_dispatch_rule_id
        except Exception as e:
            logger.error(f"Error creating dispatch rule: {str(e)}")
            raise ValueError(f"Failed to create dispatch rule: {str(e)}")
    
    async def delete_trunk(self, trunk_id: str) -> None:
        """Delete a SIP trunk from LiveKit"""
        try:
            lk_api = await self._get_api()
            
            # Call LiveKit API to delete the trunk
            delete_request = api.DeleteSIPTrunkRequest(sip_trunk_id=trunk_id)
            await lk_api.sip.delete_sip_trunk(delete_request)
        except Exception as e:
            logger.error(f"Error deleting SIP trunk: {str(e)}")
            raise ValueError(f"Failed to delete SIP trunk: {str(e)}")
    
    async def delete_dispatch_rule(self, rule_id: str) -> None:
        """Delete a SIP dispatch rule from LiveKit"""
        try:
            lk_api = await self._get_api()
            
            # Call LiveKit API to delete the dispatch rule
            delete_request = api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule_id)
            await lk_api.sip.delete_sip_dispatch_rule(delete_request)
        except Exception as e:
            logger.error(f"Error deleting dispatch rule: {str(e)}")
            raise ValueError(f"Failed to delete dispatch rule: {str(e)}")
    
    # async def unassign_trunk_from_agent(
    #     self,
    #     db: AsyncSession,
    #     mapping_id: uuid.UUID
    # ) -> None:
    #     """Remove a SIP trunk assignment from an agent profile"""
    #     try:
    #         # Retrieve the mapping
    #         mapping = await crud_sip_agent_mapping.get(db=db, id=mapping_id)
    #         if not mapping:
    #             raise ValueError(f"SIP agent mapping not found: {mapping_id}")

    #         # Use dictionary access instead of attribute access
    #         if mapping.get("dispatch_rule_id"):
    #             await self.delete_dispatch_rule(mapping["dispatch_rule_id"])
                
    #         # Delete the mapping from the database using FastCRUD
    #         await crud_sip_agent_mapping.delete(db=db, id=mapping_id)
    #     except Exception as e:
    #         logger.error(f"Error unassigning trunk from agent: {str(e)}")
    #         raise ValueError(f"Failed to unassign trunk from agent: {str(e)}")

    async def unassign_trunk_from_agent(
        self,
        db: AsyncSession,
        mapping_id: uuid.UUID
    ) -> None:
        """Remove a SIP trunk assignment from an agent profile"""
        try:
            mapping = await crud_sip_agent_mapping.get(db=db, id=mapping_id)
            if not mapping:
                logger.error(f"SIP agent mapping not found: {mapping_id}")
                raise ValueError(f"SIP agent mapping not found: {mapping_id}")

            if mapping.get("dispatch_rule_id"):
                try:
                    await self.delete_dispatch_rule(mapping["dispatch_rule_id"])
                    logger.info(f"Successfully deleted dispatch rule {mapping['dispatch_rule_id']} for mapping {mapping_id}")
                except TwirpError as e:
                    if e.code == "not_found":
                        logger.warning(f"Dispatch rule {mapping['dispatch_rule_id']} already deleted from LiveKit. Proceeding with database cleanup for mapping {mapping_id}")
                    else:
                        logger.error(f"Failed to delete dispatch rule {mapping['dispatch_rule_id']} for mapping {mapping_id}: {str(e)}")
                        raise  # Re-raise non-not_found TwirpErrors

            # Delete the mapping from the database
            await crud_sip_agent_mapping.delete(db=db, id=mapping_id)
            logger.info(f"Successfully deleted SIP agent mapping {mapping_id}")
        except ValueError as e:
            logger.error(f"Error unassigning trunk from agent for mapping {mapping_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error unassigning trunk from agent for mapping {mapping_id}: {str(e)}")
            raise ValueError(f"Failed to unassign trunk from agent: {str(e)}")

    # async def register_complete_sip_setup(
    #     self,
    #     db: AsyncSession,
    #     owner_id: uuid.UUID,
    #     name: str,
    #     description: str,
    #     sip_termination_uri: str,
    #     phone_number: str,
    #     username: str,
    #     password: str,
    #     inbound_agent_id: Optional[uuid.UUID] = None,
    #     outbound_agent_id: Optional[uuid.UUID] = None,
    #     config: Dict[str, Any] = None
    # ) -> CompleteSIPSetupResponse:
    #     """
    #     Create a complete SIP setup including:
    #     - Inbound trunk
    #     - Outbound trunk 
    #     - Dispatch rule
    #     - Agent association
    #     All in one operation with improved error handling
    #     """
    #     # Keep track of created resources for cleanup if needed
    #     created_resources = {
    #         "inbound_trunk_id": None,
    #         "outbound_trunk_id": None,
    #         "dispatch_rule_id": None
    #     }
        
    #     try:
    #         logger.info(f"Starting creation of complete SIP setup for {phone_number}")

    #         inbound_username = settings.LIVEKIT_SIP_INBOUND_USERNAME
    #         inbound_password = settings.LIVEKIT_SIP_INBOUND_PASSWORD

    #         logger.info(f"Creating inbound SIP trunk for {phone_number} with username {inbound_username} and password {inbound_password}")
            
    #         # Create inbound trunk
    #         inbound_trunk = await self.create_inbound_trunk(
    #             # name=f"{name} (Inbound)",
    #             name="test-convoi-inbound",
    #             phone_number=phone_number,
    #             username=inbound_username,  
    #             password=inbound_password
    #         )
    #         if not inbound_trunk or not inbound_trunk.sip_trunk_id:
    #             raise ValueError("Failed to create inbound SIP trunk - empty response")
            
    #         created_resources["inbound_trunk_id"] = inbound_trunk.sip_trunk_id
            
    #         # Create outbound trunk
    #         outbound_trunk = await self.create_outbound_trunk(
    #             # name=f"{name} (Outbound)",
    #             name="test-convoi-outbound",
    #             address=sip_termination_uri,
    #             username=username,
    #             password=password,
    #             phone_number=phone_number
    #         )
    #         if not outbound_trunk or not outbound_trunk.sip_trunk_id:
    #             raise ValueError("Failed to create outbound SIP trunk - empty response")
                
    #         created_resources["outbound_trunk_id"] = outbound_trunk.sip_trunk_id
            
    #         # Save trunks in database
    #         inbound_db = await crud_sip_trunk.create(
    #             db=db, 
    #             object=SIPTrunkCreateInternal(
    #                 name=f"{name} (Inbound)",
    #                 # name="lk-convoiAI-new",
    #                 description=description,
    #                 trunk_type="inbound",
    #                 sip_termination_uri=sip_termination_uri,
    #                 username=inbound_username,
    #                 password=inbound_password,
    #                 phone_number=phone_number,
    #                 owner_id=owner_id,
    #                 trunk_id=inbound_trunk.sip_trunk_id,
    #                 config=config or {}
    #             )
    #         )
            
    #         outbound_db = await crud_sip_trunk.create(
    #             db=db, 
    #             object=SIPTrunkCreateInternal(
    #                 name=f"{name} (Outbound)",
    #                 # name="lk-convoiAI-new",
    #                 description=description,
    #                 trunk_type="outbound",
    #                 sip_termination_uri=sip_termination_uri,
    #                 username=username,
    #                 password=password,
    #                 phone_number=phone_number,
    #                 owner_id=owner_id,
    #                 trunk_id=outbound_trunk.sip_trunk_id,
    #                 config=config or {}
    #             )
    #         )

    #         room_uuid = uuid.uuid4()
    #         room_name = str(room_uuid)
            
    #         # Create dispatch rule 
    #         dispatch_rule_id = await self.create_dispatch_rule(
    #             trunk_id=inbound_trunk.sip_trunk_id,
    #             room_name=room_name,
    #             phone_number=phone_number,
    #             name=f"SIP {phone_number}",
    #         )
    #         if not dispatch_rule_id:
    #             raise ValueError("Failed to create SIP dispatch rule - empty response")
                
    #         created_resources["dispatch_rule_id"] = dispatch_rule_id
            
    #         # Validate agents if provided (but don't require them)
    #         if inbound_agent_id:
    #             inbound_agent = await crud_agent_profiles.get(db=db, id=inbound_agent_id)
    #             if not inbound_agent:
    #                 raise ValueError(f"Inbound agent profile with ID {inbound_agent_id} not found")
                
    #             # Create agent reference for room-agent association
    #             await crud_agent_references.create(
    #                 db=db,
    #                 object=AgentReferenceLookupCreateInternal(
    #                     roomid=room_uuid,
    #                     agentid=inbound_agent_id
    #                 )
    #             )
            
    #         if outbound_agent_id:
    #             outbound_agent = await crud_agent_profiles.get(db=db, id=outbound_agent_id)
    #             if not outbound_agent:
    #                 raise ValueError(f"Outbound agent profile with ID {outbound_agent_id} not found")
            
    #         # Always create a mapping record to store the dispatch rule ID
    #         mapping_create = SIPAgentMappingCreateInternal(
    #             sip_trunk_id=inbound_db.id,
    #             inbound_agent_id=inbound_agent_id,
    #             outbound_agent_id=outbound_agent_id,
    #             dispatch_rule_id=dispatch_rule_id
    #         )
            
    #         mapping = await crud_sip_agent_mapping.create(db=db, object=mapping_create)
            
    #         return CompleteSIPSetupResponse(
    #             inbound_trunk=inbound_db,
    #             outbound_trunk=outbound_db,
    #             agent_mapping=mapping,
    #             dispatch_rule_id=dispatch_rule_id
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error during SIP setup creation: {str(e)}")
            
    #         # Perform cleanup of LiveKit resources
    #         await self._cleanup_resources(created_resources)
            
    #         # Re-raise the exception
    #         raise ValueError(f"Failed to create complete SIP setup: {str(e)}")


    async def register_complete_sip_setup(
        self,
        db: AsyncSession,
        owner_id: uuid.UUID,
        name: str,
        description: str,
        sip_termination_uri: str,
        phone_number: str,
        username: str,
        password: str,
        inbound_agent_id: Optional[uuid.UUID] = None,
        outbound_agent_id: Optional[uuid.UUID] = None,
        config: Dict[str, Any] = None
    ) -> CompleteSIPSetupResponse:
        """
        Create a complete SIP setup including:
        - Inbound trunk
        - Outbound trunk 
        - Dispatch rule
        - Agent association
        All in one operation with improved error handling
        """
        created_resources = {
            "inbound_trunk_id": None,
            "outbound_trunk_id": None,
            "dispatch_rule_id": None
        }
        
        try:
            logger.info(f"Starting creation of complete SIP setup for {phone_number}")

            # Validate agents if provided (fail-fast, before any creation)
            if inbound_agent_id:
                inbound_agent = await crud_agent_profiles.get(db=db, id=inbound_agent_id)
                if not inbound_agent:
                    raise ValueError(f"Inbound agent profile with ID {inbound_agent_id} not found")
            
            if outbound_agent_id:
                outbound_agent = await crud_agent_profiles.get(db=db, id=outbound_agent_id)
                if not outbound_agent:
                    raise ValueError(f"Outbound agent profile with ID {outbound_agent_id} not found")

            inbound_username = settings.LIVEKIT_SIP_INBOUND_USERNAME
            inbound_password = settings.LIVEKIT_SIP_INBOUND_PASSWORD

            logger.info(f"Creating inbound SIP trunk for {phone_number} with username {inbound_username}")

            # Create inbound trunk
            inbound_trunk = await self.create_inbound_trunk(
                name=f"{name} (Inbound)",
                phone_number=phone_number,
                username=inbound_username,
                password=inbound_password
            )
            if not inbound_trunk or not inbound_trunk.sip_trunk_id:
                raise ValueError("Failed to create inbound SIP trunk - empty response")
            created_resources["inbound_trunk_id"] = inbound_trunk.sip_trunk_id
            
            # Create outbound trunk
            outbound_trunk = await self.create_outbound_trunk(
                name=f"{name} (Outbound)",
                address=sip_termination_uri,
                username=username,
                password=password,
                phone_number=phone_number
            )
            if not outbound_trunk or not outbound_trunk.sip_trunk_id:
                raise ValueError("Failed to create outbound SIP trunk - empty response")
            created_resources["outbound_trunk_id"] = outbound_trunk.sip_trunk_id
            
            # Save trunks in database
            inbound_db = await crud_sip_trunk.create(
                db=db, 
                object=SIPTrunkCreateInternal(
                    name=f"{name} (Inbound)",
                    description=description,
                    trunk_type="inbound",
                    sip_termination_uri=sip_termination_uri,
                    username=inbound_username,
                    password=inbound_password,
                    phone_number=phone_number,
                    owner_id=owner_id,
                    trunk_id=inbound_trunk.sip_trunk_id,
                    config=config or {}
                )
            )
            
            outbound_db = await crud_sip_trunk.create(
                db=db, 
                object=SIPTrunkCreateInternal(
                    name=f"{name} (Outbound)",
                    description=description,
                    trunk_type="outbound",
                    sip_termination_uri=sip_termination_uri,
                    username=username,
                    password=password,
                    phone_number=phone_number,
                    owner_id=owner_id,
                    trunk_id=outbound_trunk.sip_trunk_id,
                    config=config or {}
                )
            )

            room_uuid = uuid.uuid4()
            room_name = str(room_uuid)
            
            # Create dispatch rule 
            dispatch_rule_id = await self.create_dispatch_rule(
                trunk_id=inbound_trunk.sip_trunk_id,
                room_name=room_name,
                phone_number=phone_number,
                name=f"SIP {phone_number}",
            )
            if not dispatch_rule_id:
                raise ValueError("Failed to create SIP dispatch rule - empty response")
            created_resources["dispatch_rule_id"] = dispatch_rule_id
            
            # Create agent reference for room-agent association
            if inbound_agent_id:
                await crud_agent_references.create(
                    db=db,
                    object=AgentReferenceLookupCreateInternal(
                        roomid=room_uuid,
                        agentid=inbound_agent_id
                    )
                )
            
            # Always create a mapping record to store the dispatch rule ID
            mapping_create = SIPAgentMappingCreateInternal(
                sip_trunk_id=inbound_db.id,
                inbound_agent_id=inbound_agent_id,
                outbound_agent_id=outbound_agent_id,
                dispatch_rule_id=dispatch_rule_id
            )
            
            mapping = await crud_sip_agent_mapping.create(db=db, object=mapping_create)
            
            return CompleteSIPSetupResponse(
                inbound_trunk=inbound_db,
                outbound_trunk=outbound_db,
                agent_mapping=mapping,
                dispatch_rule_id=dispatch_rule_id
            )
            
        except Exception as e:
            logger.error(f"Error during SIP setup creation: {str(e)}")
            
            # Perform cleanup of LiveKit resources (database rollback handled by endpoint)
            await self._cleanup_resources(created_resources)
            
            # Re-raise the exception
            raise ValueError(f"Failed to create complete SIP setup: {str(e)}")

    async def _cleanup_resources(self, created_resources: Dict[str, Any]) -> None:
        """Clean up LiveKit API resources when a transaction fails."""
        cleanup_errors = []
        
        # Delete dispatch rule
        if created_resources["dispatch_rule_id"]:
            try:
                await self.delete_dispatch_rule(created_resources["dispatch_rule_id"])
            except Exception as e:
                error_msg = f"Failed to delete dispatch rule: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Delete outbound trunk
        if created_resources["outbound_trunk_id"]:
            try:
                await self.delete_trunk(created_resources["outbound_trunk_id"])
            except Exception as e:
                error_msg = f"Failed to delete outbound trunk: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Delete inbound trunk
        if created_resources["inbound_trunk_id"]:
            try:
                await self.delete_trunk(created_resources["inbound_trunk_id"])
            except Exception as e:
                error_msg = f"Failed to delete inbound trunk: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        if cleanup_errors:
            logger.error(f"Encountered {len(cleanup_errors)} errors during cleanup: {', '.join(cleanup_errors)}")
        else:
            logger.info("Cleanup completed successfully")

    # async def _cleanup_resources(self, created_resources: Dict[str, Any]) -> None:
    #     """Clean up LiveKit API resources when a transaction fails."""
    #     cleanup_errors = []
        
    #     # Delete dispatch rule
    #     if created_resources["dispatch_rule_id"]:
    #         try:
    #             await self.delete_dispatch_rule(created_resources["dispatch_rule_id"])
    #         except Exception as e:
    #             error_msg = f"Failed to delete dispatch rule: {str(e)}"
    #             logger.error(error_msg)
    #             cleanup_errors.append(error_msg)
        
    #     # Delete outbound trunk
    #     if created_resources["outbound_trunk_id"]:
    #         try:
    #             await self.delete_trunk(created_resources["outbound_trunk_id"])
    #         except Exception as e:
    #             error_msg = f"Failed to delete outbound trunk: {str(e)}"
    #             logger.error(error_msg)
    #             cleanup_errors.append(error_msg)
        
    #     # Delete inbound trunk
    #     if created_resources["inbound_trunk_id"]:
    #         try:
    #             await self.delete_trunk(created_resources["inbound_trunk_id"])
    #         except Exception as e:
    #             error_msg = f"Failed to delete inbound trunk: {str(e)}"
    #             logger.error(error_msg)
    #             cleanup_errors.append(error_msg)
        
    #     if cleanup_errors:
    #         logger.error(f"Encountered {len(cleanup_errors)} errors during cleanup: {', '.join(cleanup_errors)}")
    #     else:
    #         logger.info("Cleanup completed successfully")
    
    async def handle_inbound_call(
        self,
        db: AsyncSession,
        to_number: str,
        from_number: str,
        call_sid: str,
        call_direction: SIPCallDirection
    ) -> Dict[str, Any]:
        """
        Processes an incoming SIP call, creates a database record, and
        prepares the data required for the TwiML response.
        """
        logger.info(f"Handling inbound call to {to_number} from {from_number}")

        # Find the SIP trunk associated with the 'To' number
        trunk = await crud_sip_trunk.get_by_phone_number(db, phone_number=to_number)
        if not trunk:
            logger.error(f"No SIP trunk found for number: {to_number}")
            raise HTTPException(status_code=404, detail="No SIP trunk found for this phone number.")

        # Find the agent mapping for this trunk
        mappings = await crud_sip_agent_mapping.get_by_trunk_id(db, trunk_id=trunk["id"])
        if not mappings:
            logger.error(f"No agent mapping found for trunk: {trunk['id']}")
            raise HTTPException(status_code=404, detail="No agent mapping found for this trunk.")

        mapping = mappings[0]
        agent_id = mapping.get("inbound_agent_id")
        
        # Validate inbound agent
        if not agent_id:
            logger.error(f"Inbound agent not configured for trunk: {trunk['id']}")
            raise HTTPException(status_code=400, detail="Inbound agent not configured for this trunk.")
        
        agent = await crud_agent_profiles.get(db, id=agent_id)
        if not agent:
            logger.error(f"Agent profile with ID {agent_id} not found.")
            raise HTTPException(status_code=404, detail=f"Agent profile with ID {agent_id} not found.")
            
        # Get the owner_id from the agent profile
        owner_id = agent.owner_id

        # CONSTRUCT THE ROOM ID BASED ON LOGS
        # The room name will be in the format: call-<from_number>_<call_sid>
        room_id = f"call-_{from_number}_{call_sid}"
        logger.info(f"Before new connection record for call to room: {room_id}")
        # logger.info(f"{'room_id': room_id, 'agent_id': agent_id, 'owner_id': owner_id, 'Ahtasham call_id': call_sid}")
        # Create a new connection record for this call
        try:
            connection = await crud_connections.create_connection(
                db=db, 
                room_id=room_id, 
                agent_id=agent_id, 
                owner_id=owner_id,
                call_id=call_sid
            )
            logger.info(f"Created new connection record for call to room: {room_id}")
        except Exception as e:
            logger.error(f"Failed to create connection record: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create connection: {str(e)}")

        # Create a new SIP call record in the database
        await crud_sip_calls.create_call_record(
            db=db,
            call_id=call_sid,
            room_id=room_id,
            direction=call_direction,
            phone_number=from_number,
            trunk_id=trunk["id"],
            agent_id=agent_id,
            call_metadata={"to_number": to_number}   # ✅ correct keyword
        )
        logger.info(f"Created new SIPCall record for CallSid: {call_sid}")

        # Prepare data for TwiML response
        response_data = {
            "room_id": room_id,
            "sip_host": settings.LIVEKIT_SIP_HOST,
            "username": trunk["username"],
            "password": trunk["password"]
        }

        logger.info(f"TwiML response data: {response_data}")
        return response_data
    

    # async def create_outbound_call(
    #     self,
    #     db: AsyncSession,
    #     phone_number: str,
    #     agent_id: uuid.UUID,
    #     trunk_id: Optional[uuid.UUID] = None,
    #     attributes: Optional[Dict[str, str]] = None
    # ) -> Tuple[SIPParticipantInfo, uuid.UUID]:
    #     """Create an outbound SIP call to a phone number"""
    #     try:
    #         lk_api = await self._get_api()
            
    #         # Get the SIP trunk to use
    #         if trunk_id:
    #             trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
    #             if not trunk:
    #                 raise ValueError(f"SIP trunk not found: {trunk_id}")
    #         else:
    #             # Find a suitable outbound trunk
    #             trunks = await crud_sip_trunk.get_by_type(db=db, trunk_type="outbound")
    #             if not trunks or len(trunks) == 0:
    #                 raise ValueError("No outbound SIP trunk available")
    #             trunk = trunks[0]
                
    #         if trunk["trunk_type"] != "outbound":
    #             raise ValueError(f"Trunk {trunk_id} is not an outbound trunk")
                
    #         # Verify the agent exists
    #         agent = await crud_agent_profiles.get(db=db, id=agent_id)
    #         if not agent:
    #             raise ValueError(f"Agent profile not found: {agent_id}")
                
    #         # Create a unique room name for this call
    #         room_uuid = uuid.uuid4()
    #         room_name = str(room_uuid)
            
    #         # Create the agent reference for the room
    #         await crud_agent_references.create(
    #             db=db,
    #             object=AgentReferenceLookupCreateInternal(
    #                 roomid=room_name,
    #                 agentid=agent_id
    #             )
    #         )
            
    #         # Set up participant attributes
    #         participant_attrs = attributes or {}
    #         participant_attrs.update({
    #             "sip.direction": "outbound",
    #             "sip.phoneNumber": phone_number,
    #             "direction": "outbound"
    #         })
            
    #         # Create the participant request
    #         request = api.CreateSIPParticipantRequest(
    #             sip_trunk_id=trunk["trunk_id"],
    #             sip_call_to=phone_number,
    #             sip_number=trunk["phone_number"],
    #             room_name=room_name,
    #             participant_identity=f"sip-outbound-{phone_number}",
    #             participant_name=f"SIP Call to {phone_number}",
    #             participant_attributes=participant_attrs,
    #             play_ringtone=True,
    #             hide_phone_number=False,
    #             wait_until_answered=True
    #         )
            
    #         response = await lk_api.sip.create_sip_participant(request)
            
    #         # Record the call in the database
    #         await crud_sip_calls.create_call_record(
    #             db=db,
    #             call_id=response.sip_call_id,
    #             room_id=room_name,
    #             direction=SIPCallDirection.OUTBOUND,
    #             phone_number=phone_number,
    #             trunk_id=trunk["id"],
    #             agent_id=agent_id,
    #             call_metadata=participant_attrs
    #         )
            
    #         logger.info(f"Initiated outbound SIP call to {phone_number}, call ID: {response.sip_call_id}")
    #         return response, room_name
    #     except Exception as e:
    #         logger.error(f"Error creating outbound SIP call: {str(e)}")
    #         raise ValueError(f"Failed to create outbound SIP call: {str(e)}")


    async def create_outbound_call(
        self,
        db: AsyncSession,
        phone_number: str,
        agent_id: uuid.UUID,
        trunk_id: Optional[uuid.UUID] = None,
        attributes: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str, SIPParticipantInfo]:
        """Create an outbound SIP call to a phone number"""
        try:
            lk_api = await self._get_api()
            
            # Get the SIP trunk to use
            if trunk_id:
                trunk = await crud_sip_trunk.get(db=db, id=trunk_id)
                if not trunk:
                    raise ValueError(f"SIP trunk not found: {trunk_id}")
            else:
                # Find a suitable outbound trunk
                trunks = await crud_sip_trunk.get_by_type(db=db, trunk_type="outbound")
                if not trunks or len(trunks) == 0:
                    raise ValueError("No outbound SIP trunk available")
                trunk = trunks[0]
                
            if trunk["trunk_type"] != "outbound":
                raise ValueError(f"Trunk {trunk_id} is not an outbound trunk")
                
            # Verify the agent exists
            agent = await crud_agent_profiles.get(db=db, id=agent_id)
            if not agent:
                raise ValueError(f"Agent profile not found: {agent_id}")
            
            # Get the owner_id from the agent profile
            owner_id = agent.owner_id
                
            # Create a unique room name for this call
            room_uuid = uuid.uuid4()
            room_name = str(room_uuid)
            
            # Create the connection record
            connection = await crud_connections.create_connection(
                db=db, 
                room_id=room_name,
                agent_id=agent_id,
                owner_id=owner_id
            )
            
            # Set up participant attributes
            participant_attrs = attributes or {}
            participant_attrs.update({
                "sip.direction": "outbound",
                "sip.phoneNumber": phone_number,
                "direction": "outbound"
            })
            
            # Create the participant request
            request = api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk["trunk_id"],
                sip_call_to=phone_number,
                sip_number=trunk["phone_number"],
                room_name=room_name,
                participant_identity=f"sip-outbound-{phone_number}",
                participant_name=f"SIP Call to {phone_number}",
                participant_attributes=participant_attrs,
                play_ringtone=True,
                hide_phone_number=False,
                wait_until_answered=True,
                krisp_enabled=True  # Add Krisp noise cancellation
            )
            
            response = await lk_api.sip.create_sip_participant(request)

            # --- THIS IS THE CORRECTED PART ---
            # The correct class is CreateAgentDispatchRequest
            # The correct method is agent_dispatch.create_dispatch
            dispatch_request = api.CreateAgentDispatchRequest(
                agent_name="convoi-telephone-agent",
                room=room_name,
                metadata=json.dumps({
                    "phone_number": phone_number,
                    "trunk_id": str(trunk["trunk_id"]),
                    "participant_attributes": participant_attrs,
                })
            )

            # Dispatch via agent dispatch service:
            # The create_dispatch method returns a CreateAgentDispatchResponse
            # which contains the job_id
            job_response = await lk_api.agent_dispatch.create_dispatch(dispatch_request)
            logger.info(f"Created agent job: {job_response.id} for outbound call to {phone_number}")
            
            # You would record the call record after this and tie it to the job_id
            await crud_sip_calls.create_call_record(
                db=db,
                call_id=job_response.id,
                room_id=room_name,
                direction=SIPCallDirection.OUTBOUND,
                phone_number=phone_number,
                trunk_id=trunk["id"],
                agent_id=agent_id,
                call_metadata=participant_attrs
            )
            
            logger.info(f"Initiated outbound call via agent dispatch to {phone_number}")

            return room_name, job_response.id, response

        except Exception as e:
            logger.error(f"Error creating outbound SIP call: {str(e)}")
            raise ValueError(f"Failed to create outbound SIP call: {str(e)}")


    async def get_outbound_call_status(
        self,
        db: AsyncSession,
        call_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the status of an outbound SIP call"""
        try:
            call = await with_worker_db(
                lambda db: crud_sip_calls.get_by_call_id(db=db, call_id=call_id)
            )
            
            if not call:
                return None
            
            # CORRECTED: Changed all attribute access (e.g., call.call_id)
            # to dictionary key access (e.g., call['call_id']).
            return {
                "call_id": call['call_id'],
                "room_id": call['room_id'],
                "status": call['status'],
                "direction": call['direction'],
                "phone_number": call['phone_number'],
                "created_at": call['created_at'].isoformat() if call['created_at'] else None,
                "answered_at": call['answered_at'].isoformat() if call['answered_at'] else None,
                "completed_at": call['completed_at'].isoformat() if call['completed_at'] else None,
                "duration_seconds": call['duration_seconds'],
                "success": call['success'],
                "agent_id": str(call['agent_id']) if call['agent_id'] else None
            }
        except Exception as e:
            logger.error(f"Error getting outbound call status: {str(e)}")
            return None

    async def dispatch_agent_for_connection(self, room_id: str, agent_profile: Any) -> api.Job:
        """Dispatches a LiveKit agent to a room for an internet call."""
        lk_api = await self._get_api()
        try:
            dispatch_request = api.CreateAgentDispatchRequest(
                agent_name="convoi-telephone-agent",
                room=str(room_id),
                metadata=json.dumps({
                    "type": "internet_call",
                    "agent_id": str(agent_profile.id),
                    "room_id": str(room_id),
                })
            )
            job = await lk_api.agent_dispatch.create_dispatch(dispatch_request)
            logger.info(f"Dispatched agent job {job.id} for room {room_id}")
            return job
        except Exception as e:
            logger.error(f"Failed to dispatch agent for room {room_id}: {e}")
            raise


# Create a singleton instance
sip_factory = SIPFactory()