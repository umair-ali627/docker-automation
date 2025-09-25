# app/services/sip_call_manager.py
import asyncio
import logging
import uuid
from typing import Dict, Optional, Set, Any
from datetime import datetime, timezone

from livekit import rtc, api
from livekit.protocol.sip import TransferSIPParticipantRequest, SIPCallStatus

from ..crud.crud_sip import crud_sip_calls
from ..utils.db_utils import with_worker_db
from ..core.config import settings

logger = logging.getLogger("sip-call-manager")

class SIPCallManager:
    """
    Manages active SIP calls and provides utility functions for controlling them.
    """
    
    def __init__(self):
        self._active_calls: Dict[str, Dict[str, Any]] = {}
        self._lk_api: Optional[api.LiveKitAPI] = None
    
    async def _get_api(self) -> api.LiveKitAPI:
        """Lazy initialization of LiveKit API"""
        if self._lk_api is None:
            # Make sure the LiveKit URL is properly formatted
            livekit_url = settings.LIVEKIT_HOST
            if not livekit_url.startswith(("http://", "https://")):
                livekit_url = f"https://{livekit_url}"
            
            self._lk_api = api.LiveKitAPI(
                url=livekit_url,
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
            )
        
        return self._lk_api
    
    def register_call(
        self, 
        call_id: str, 
        room_name: str, 
        phone_number: str,
        participant_identity: str,
        direction: str = "inbound",
        agent_id: Optional[uuid.UUID] = None,
        trunk_id: Optional[uuid.UUID] = None
    ) -> None:
        """Register an active SIP call"""
        self._active_calls[call_id] = {
            "start_time": datetime.now(timezone.utc),
            "room_name": room_name,
            "phone_number": phone_number,
            "participant_identity": participant_identity,
            "direction": direction,
            "agent_id": agent_id,
            "trunk_id": trunk_id,
            "status": SIPCallStatus.ACTIVE,
        }
        logger.info(f"Registered SIP call {call_id} from {phone_number}")
    
    def unregister_call(self, call_id: str) -> None:
        """Unregister a SIP call"""
        if call_id in self._active_calls:
            self._active_calls.pop(call_id)
            logger.info(f"Unregistered SIP call {call_id}")
    
    def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a SIP call"""
        return self._active_calls.get(call_id)
    
    def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
        """Get all active SIP calls"""
        return self._active_calls.copy()
    
    async def transfer_call(
        self, 
        call_id: str, 
        transfer_to: str, 
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Transfer a SIP call to another number or SIP URI.
        
        Args:
            call_id: The ID of the call to transfer
            transfer_to: Phone number or SIP URI to transfer to
            headers: Additional SIP headers for the transfer
            
        Returns:
            bool: True if transfer was successful
        """
        if call_id not in self._active_calls:
            logger.error(f"Cannot transfer call {call_id}: call not found")
            return False
        
        call_info = self._active_calls[call_id]
        
        try:
            lk_api = await self._get_api()
            
            # Create transfer request
            transfer_request = TransferSIPParticipantRequest(
                participant_identity=call_info["participant_identity"],
                room_name=call_info["room_name"],
                transfer_to=transfer_to,
                play_dialtone=True
            )
            
            # Add optional headers
            if headers:
                for key, value in headers.items():
                    transfer_request.headers[key] = value
            
            # Execute transfer
            await lk_api.sip.transfer_sip_participant(transfer_request)
            
            # Update call record in database
            try:
                await with_worker_db(
                    lambda db: crud_sip_calls.update(
                        db=db,
                        call_id=call_id,
                        object={
                            "status": SIPCallStatus.COMPLETED.value,
                            "completed_at": datetime.now(timezone.utc),
                            "metadata": {
                                "transfer_target": transfer_to,
                                "transfer_time": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                )
            except Exception as e:
                logger.error(f"Error updating call record for transfer: {e}")
            
            # Remove from active calls
            self.unregister_call(call_id)
            
            logger.info(f"Successfully transferred call {call_id} to {transfer_to}")
            return True
            
        except Exception as e:
            logger.error(f"Error transferring call {call_id}: {e}")
            return False
    
    async def hangup_call(self, call_id: str) -> bool:
        """
        Hang up a SIP call.
        
        Note: Currently LiveKit doesn't have a direct API to hang up a call.
        This method will update database records but the call needs to be
        ended by the participant disconnecting.
        
        Returns:
            bool: True if successful
        """
        if call_id not in self._active_calls:
            logger.error(f"Cannot hang up call {call_id}: call not found")
            return False
        
        try:
            # Update call record in database
            await with_worker_db(
                lambda db: crud_sip_calls.mark_call_completed(
                    db=db,
                    call_id=call_id,
                    success=True,
                    metadata={"ended_by": "system", "end_reason": "hangup"}
                )
            )
            
            # Remove from active calls
            self.unregister_call(call_id)
            
            logger.info(f"Marked call {call_id} as hung up")
            return True
            
        except Exception as e:
            logger.error(f"Error hanging up call {call_id}: {e}")
            return False
    
    async def aclose(self):
        """Clean up resources"""
        if self._lk_api:
            await self._lk_api.aclose()
            self._lk_api = None

# Create a singleton instance
sip_call_manager = SIPCallManager()