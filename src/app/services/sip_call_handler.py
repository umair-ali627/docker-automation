import asyncio
import logging
import uuid
from typing import Optional, Dict, Any

from livekit import rtc
from livekit.agents import metrics, JobContext

from ..services.agent_profile import setup_agent_with_profile, get_sip_information
from ..utils.db_utils import with_worker_db
from ..crud.crud_sip import crud_sip_calls, crud_sip_agent_mapping, crud_sip_trunk
from ..crud.crud_agent_reference import crud_agent_references
from ..crud.crud_agent_profiles import crud_agent_profiles

logger = logging.getLogger("sip-call-handler")

def is_sip_participant(participant: rtc.RemoteParticipant) -> bool:
    """
    Determine if a participant is a SIP participant.
    """
    return participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP

def is_sip_room(room_name: str) -> bool:
    """
    Determine if a room name indicates a SIP call (using LiveKit's naming pattern).
    """
    return room_name.startswith("sip-inbound-") or room_name.startswith("sip-outbound-")

async def handle_sip_call(ctx: JobContext, participant: rtc.RemoteParticipant, usage_collector: metrics.UsageCollector):
    """
    Specialized handler for SIP calls.
    
    Args:
        ctx: JobContext for the current job
        participant: The SIP participant
        usage_collector: Metrics collector for tracking usage
    """
    room_name = ctx.room.name
    logger.info(f"Processing SIP call in room: {room_name}")
    
    # Determine if this is inbound or outbound from room name
    call_direction = "inbound" if "inbound" in room_name else "outbound"
    
    # Create a synthetic room ID for database purposes
    room_uuid = None
    try:
        # Try to use room name as UUID if possible
        room_uuid = uuid.UUID(room_name)
    except (ValueError, TypeError):
        # Create a deterministic UUID from the room name
        room_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, room_name)
        logger.info(f"Created deterministic UUID {room_uuid} from room name {room_name}")
    
    # Extract SIP information from participant attributes and create metadata
    sip_metadata = extract_sip_metadata(participant, call_direction)
    logger.info(f"Extracted SIP metadata: {sip_metadata}")
    
    # Get appropriate agent ID for this call
    agent_id = await get_agent_for_sip_call(room_uuid, participant, sip_metadata)
    
    logger.info(f"SIP call details - Direction: {sip_metadata.get('call_direction')}, "
                f"Phone: {sip_metadata.get('phone_number')}, Agent ID: {agent_id}")
    
    # Create the agent for the SIP participant
    agent = await setup_agent_with_profile(
        ctx=ctx,
        participant=participant,
        agent_id=agent_id 
    )
    
    # Set up metrics collection
    @agent.on("metrics_collected")
    def _on_metrics_collected(metrics_data):
        metrics.log_metrics(metrics_data)
        usage_collector.collect(metrics_data)
    
    # Register call completion handler for metrics and database updates
    async def on_call_complete():
        try:
            summary = usage_collector.get_summary()
            logger.info(f"SIP call usage: {summary}")
            
            # Update call record with metrics
            call_id = sip_metadata.get('call_id') or participant.sid
            if call_id:
                await with_worker_db(
                    lambda db: crud_sip_calls.mark_call_completed(
                        db=db,
                        call_id=call_id,
                        success=True,
                        metadata={
                            "metrics": summary,
                            "total_tokens": summary.get("tokens", 0),
                            "total_duration": summary.get("duration", 0)
                        }
                    )
                )
                logger.info(f"Updated SIP call record with metrics")
        except Exception as e:
            logger.error(f"Error in SIP call completion handler: {e}")
    
    # Register shutdown callback
    ctx.add_shutdown_callback(on_call_complete)
    
    # Set up disconnect handler
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(p):
        if p.identity == participant.identity and is_sip_participant(p):
            logger.info(f"SIP participant disconnected: {p.identity}")
            # The completion metrics will be handled by the shutdown callback


def extract_sip_metadata(participant: rtc.RemoteParticipant, default_direction: str = "inbound") -> Dict[str, Any]:
    """
    Extract SIP metadata from participant attributes.
    
    Args:
        participant: The SIP participant
        default_direction: Default call direction if not found in attributes
        
    Returns:
        Dictionary of SIP metadata
    """
    metadata = {
        "sip_call_detected": True,
        "call_direction": default_direction,
        "phone_number": None,
        "trunk_id": None,
        "call_id": None,
    }
    
    # Extract phone number
    for key in ["sip.phoneNumber", "sip.trunkPhoneNumber"]:
        if key in participant.attributes:
            metadata["phone_number"] = participant.attributes[key]
            break
    
    # Extract trunk ID
    if "sip.trunkID" in participant.attributes:
        metadata["trunk_id"] = participant.attributes["sip.trunkID"]
    
    # Extract call ID
    if "sip.callID" in participant.attributes:
        metadata["call_id"] = participant.attributes["sip.callID"]
    elif "sip.twilio.callSid" in participant.attributes:
        metadata["call_id"] = participant.attributes["sip.twilio.callSid"]
    
    # Extract rule ID
    if "sip.ruleID" in participant.attributes:
        metadata["rule_id"] = participant.attributes["sip.ruleID"]
    
    # Add all sip attributes for reference
    for key, value in participant.attributes.items():
        if key.startswith("sip."):
            metadata[key] = value
    
    return metadata


async def get_agent_for_sip_call(
    room_id: uuid.UUID, 
    participant: rtc.RemoteParticipant,
    sip_metadata: Dict[str, Any]
) -> Optional[uuid.UUID]:
    """
    Determine the appropriate agent ID for a SIP call.
    
    This function tries several approaches:
    1. Look up agent by trunk ID from SIP metadata
    2. Look up agent by rule ID from SIP metadata
    3. Fall back to looking for a reference in the database
    
    Returns:
        UUID of the agent profile to use, or None if not found
    """
    agent_id = None
    
    # Try to get agent from trunk ID
    trunk_id = sip_metadata.get("trunk_id")
    if trunk_id:
        try:
            # Get trunk from database using LiveKit trunk ID
            trunk = await with_worker_db(
                lambda db: crud_sip_trunk.get_by_trunk_id(db=db, trunk_id=trunk_id)
            )
            
            if trunk:
                # Get agent mapping for this trunk
                mappings = await with_worker_db(
                    lambda db: crud_sip_agent_mapping.get_by_trunk_id(db=db, trunk_id=trunk["id"])
                )
                
                if mappings and len(mappings) > 0:
                    mapping = mappings[0]
                    direction = sip_metadata.get("call_direction", "inbound")
                    
                    # Choose agent based on direction
                    if direction == "inbound" and mapping.get("inbound_agent_id"):
                        agent_id = mapping.get("inbound_agent_id")
                        logger.info(f"Using inbound agent {agent_id} for trunk {trunk_id}")
                    elif direction == "outbound" and mapping.get("outbound_agent_id"):
                        agent_id = mapping.get("outbound_agent_id")
                        logger.info(f"Using outbound agent {agent_id} for trunk {trunk_id}")
        except Exception as e:
            logger.error(f"Error looking up agent by trunk ID: {e}")
    
    # Try to get agent from rule ID
    if not agent_id and "rule_id" in sip_metadata:
        rule_id = sip_metadata["rule_id"]
        try:
            mapping = await with_worker_db(
                lambda db: crud_sip_agent_mapping.get_by_dispatch_rule_id(db=db, rule_id=rule_id)
            )
            
            if mapping:
                direction = sip_metadata.get("call_direction", "inbound")
                if direction == "inbound" and mapping.get("inbound_agent_id"):
                    agent_id = mapping.get("inbound_agent_id")
                    logger.info(f"Using inbound agent {agent_id} for rule {rule_id}")
                elif direction == "outbound" and mapping.get("outbound_agent_id"):
                    agent_id = mapping.get("outbound_agent_id")
                    logger.info(f"Using outbound agent {agent_id} for rule {rule_id}")
        except Exception as e:
            logger.error(f"Error looking up agent by rule ID: {e}")
    
    # If still no agent, try to get default agent
    if not agent_id:
        try:
            default_profile = await with_worker_db(
                lambda db: crud_agent_profiles.get_default(db=db)
            )
            if default_profile:
                agent_id = default_profile.id
                logger.info(f"Using default agent profile {agent_id}")
        except Exception as e:
            logger.error(f"Error getting default agent profile: {e}")
    
    return agent_id

async def handle_sip_participant_joined(ctx: JobContext, participant: rtc.RemoteParticipant, usage_collector: metrics.UsageCollector = None):
    """
    Handler for when a new SIP participant joins a room that already has an active session.
    
    Args:
        ctx: JobContext for the current job
        participant: The new SIP participant
        usage_collector: Optional shared metrics collector
    """
    logger.info(f"Handling new SIP participant join: {participant.identity}")
    
    # If no usage collector was provided, create a new one
    if not usage_collector:
        usage_collector = metrics.UsageCollector()
    
    # Create a separate agent for this SIP participant
    try:
        # Get SIP-specific information
        room_uuid = None
        try:
            room_uuid = uuid.UUID(ctx.room.name)
        except (ValueError, TypeError):
            pass
        
        agent_id, sip_metadata = await get_sip_information(
            room_id=room_uuid,
            participant=participant
        )
        
        # Create the agent
        sip_agent = await setup_agent_with_profile(
            ctx=ctx,
            participant=participant,
            agent_id=agent_id
        )
        
        # Set up metrics collection
        @sip_agent.on("metrics_collected")
        def _on_sip_metrics_collected(metrics_data):
            metrics.log_metrics(metrics_data)
            if usage_collector:
                usage_collector.collect(metrics_data)
        
        logger.info(f"Started new agent for SIP participant {participant.identity}")
        
        # Return the agent in case further customization is needed
        return sip_agent
    
    except Exception as e:
        logger.error(f"Failed to start agent for SIP participant: {e}")
        return None