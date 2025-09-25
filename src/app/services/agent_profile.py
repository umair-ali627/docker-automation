import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
import uuid
import inspect
import os

from livekit import rtc
from livekit.agents import llm, JobContext
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai
from livekit.agents.llm import FunctionContext

from ..core.config import settings
from ..crud.crud_agent_profiles import crud_agent_profiles
from ..crud.crud_sip import crud_sip_calls, crud_sip_trunk, crud_sip_agent_mapping
from ..crud.crud_function_tool import crud_function_tools
from ..schemas.sip import SIPCallDirection, SIPCallCreateInternal, SIPCallStatus
from ..utils.db_utils import with_worker_db
from ..services.agent_rag import rag_service
from ..services.provider_factory import ProviderFactory
from ..schemas.provider_types import STTProvider
from ..services.function_integration import function_integration
from ..services.function_executor import function_executor

logger = logging.getLogger("agent-profile-service")

async def create_voice_agent(
    ctx: JobContext, 
    vad,
    profile_config,
    func_ctx=None,
    before_llm_cb=None
) -> VoicePipelineAgent:
    """
    Create a voice agent using the provided profile configuration.
    """
    # Create the initial chat context with the system prompt
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=profile_config.get("system_prompt")
    )
    
    # Create providers using factory methods
    try:
        llm_instance = ProviderFactory.create_llm(
            provider=profile_config.get("llm_provider"),
            options=profile_config.get("llm_options", {})
        )
        
        tts_instance = ProviderFactory.create_tts(
            provider=profile_config.get("tts_provider"),
            options=profile_config.get("tts_options", {})
        )
        
        # Determine if using telephony-optimized model
        is_telephony = False
        if ctx and hasattr(ctx, 'room') and ctx.room:
            for participant in ctx.room.remote_participants.values():
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    is_telephony = True
                    break
        
        stt_instance = ProviderFactory.create_stt(
            provider=profile_config.get("stt_provider"),
            options=profile_config.get("stt_options", {}),
            is_telephony=is_telephony
        )
    except NotImplementedError as e:
        logger.warning(f"Provider not implemented: {e}. Falling back to defaults.")
        # Fall back to OpenAI/Deepgram if selected provider not yet implemented
        llm_instance = openai.LLM(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o"
        )
        tts_instance = openai.TTS(
            api_key=settings.OPENAI_API_KEY,
            voice="alloy"
        )
        stt_instance = deepgram.STT(
            api_key=settings.DEEPGRAM_API_KEY,
            model="nova-3-general" if not is_telephony else "nova-2-phonecall"
        )

    # Create the voice pipeline agent with the configured providers
    agent = VoicePipelineAgent(
        vad=vad,
        stt=stt_instance,
        llm=llm_instance,
        tts=tts_instance,
        chat_ctx=initial_ctx,
        fnc_ctx=func_ctx,
        allow_interruptions=profile_config.get("allow_interruptions", True),
        interrupt_speech_duration=profile_config.get("interrupt_speech_duration", 0.5),
        interrupt_min_words=profile_config.get("interrupt_min_words", 0),
        min_endpointing_delay=profile_config.get("min_endpointing_delay", 0.5),
        max_endpointing_delay=profile_config.get("max_endpointing_delay", 6.0),
        max_nested_fnc_calls=profile_config.get("max_nested_function_calls", 1),
        before_llm_cb=before_llm_cb,
    )
    
    return agent

async def get_sip_information(
    room_id: uuid.UUID,
    participant: rtc.RemoteParticipant
) -> Tuple[Optional[uuid.UUID], Dict[str, Any]]:
    """
    Get SIP information for a SIP participant.
    
    Returns:
        Tuple of (agent_id, call_metadata)
    """
    call_metadata = {
        "sip_call_detected": True,
        "call_direction": None,
        "phone_number": None,
        "trunk_id": None
    }
    
    # Extract SIP participant attributes with dot notation
    phone_number = None
    for attr_key in ["sip.phoneNumber", "sip.trunkPhoneNumber", "phoneNumber", "phone_number"]:
        if attr_key in participant.attributes:
            phone_number = participant.attributes[attr_key]
            if phone_number:
                # Clean phone number format
                phone_number = phone_number.replace("sip:", "").split("@")[0]
                call_metadata["phone_number"] = phone_number
                break
    
    # Extract call direction from headers or room name
    call_direction = None
    for dir_key in ["sip.direction", "direction"]:
        if dir_key in participant.attributes:
            call_direction = participant.attributes[dir_key]
            break
    
    # If direction not found in attributes, infer from room name if possible
    if not call_direction and room_id:
        try:
            room_name = str(room_id)
            if "inbound" in room_name:
                call_direction = "inbound"
            elif "outbound" in room_name:
                call_direction = "outbound"
        except:
            pass
    
    # Default to inbound if still not determined
    if not call_direction:
        call_direction = "inbound"
    
    call_metadata["call_direction"] = call_direction
    
    # Try to get trunk ID from participant attributes
    trunk_id = None
    trunk_id_str = None
    if "sip.trunkID" in participant.attributes:
        trunk_id_str = participant.attributes["sip.trunkID"]
    
    if trunk_id_str:
        try:
            # Try looking up by LiveKit trunk ID
            trunk = await with_worker_db(
                lambda db: crud_sip_trunk.get_by_trunk_id(db=db, trunk_id=trunk_id_str)
            )
            if trunk:
                trunk_id = trunk["id"]
            else:
                # If not found, save the string version
                call_metadata["trunk_id_str"] = trunk_id_str
        except Exception as e:
            logger.warning(f"Error looking up trunk by ID {trunk_id_str}: {e}")
            # Still save the string version even if lookup fails
            call_metadata["trunk_id_str"] = trunk_id_str
    
    # If we have a phone number but no trunk ID, try looking up by phone number
    if phone_number and not trunk_id:
        try:
            trunk = await with_worker_db(
                lambda db: crud_sip_trunk.get_by_phone_number(db=db, phone_number=phone_number)
            )
            if trunk:
                trunk_id = trunk["id"]
                trunk_id_str = trunk["trunk_id"]
        except Exception as e:
            logger.warning(f"Error looking up trunk by phone number {phone_number}: {e}")
    
    if trunk_id:
        call_metadata["trunk_id"] = trunk_id
    
    # Get the rule ID if present
    if "sip.ruleID" in participant.attributes:
        call_metadata["rule_id"] = participant.attributes["sip.ruleID"]
    
    # Get the call ID
    if "sip.callID" in participant.attributes:
        call_metadata["call_id"] = participant.attributes["sip.callID"]
    
    # Include all raw SIP attributes for reference and debugging
    for key, value in participant.attributes.items():
        if key.startswith("sip."):
            clean_key = key.replace(".", "_")  # Replace dots for database compatibility
            call_metadata[clean_key] = value
    
    # Find the appropriate agent based on call direction and trunk
    agent_id = None
    if trunk_id:
        try:
            # Get agent mappings for this trunk
            mappings = await with_worker_db(
                lambda db: crud_sip_agent_mapping.get_by_trunk_id(db=db, trunk_id=trunk_id)
            )
            
            if mappings and len(mappings) > 0:
                mapping = mappings[0]  # Get the first mapping
                
                # Choose agent based on direction
                if call_direction == "inbound" and mapping.get("inbound_agent_id"):
                    agent_id = mapping.get("inbound_agent_id")
                    logger.info(f"Using inbound agent {agent_id} for SIP call")
                elif call_direction == "outbound" and mapping.get("outbound_agent_id"):
                    agent_id = mapping.get("outbound_agent_id")
                    logger.info(f"Using outbound agent {agent_id} for SIP call")
                else:
                    # Fallback to any available agent in the mapping
                    agent_id = mapping.get("inbound_agent_id") or mapping.get("outbound_agent_id")
                    if agent_id:
                        logger.info(f"Using fallback agent {agent_id} for SIP call")
        except Exception as e:
            logger.error(f"Error retrieving SIP agent mapping: {e}")
    
    # Record the SIP call in the database
    if room_id and participant.sid:
        try:
            call_id = participant.sid
            db_status = SIPCallStatus.INITIATED
            
            # Check if call already exists in the database
            existing_call = await with_worker_db(
                lambda db: crud_sip_calls.get_by_call_id(db=db, call_id=call_id)
            )
            
            if not existing_call:
                # Create a new call record
                await with_worker_db(
                    lambda db: crud_sip_calls.create_call_record(
                        db=db,
                        call_id=call_id,
                        room_id=room_id,
                        direction=call_metadata["call_direction"],
                        phone_number=call_metadata.get("phone_number", "unknown"),
                        trunk_id=call_metadata.get("trunk_id"),
                        agent_id=agent_id,
                        metadata=participant.attributes
                    )
                )
                logger.info(f"Created SIP call record for {call_id} in database")
            else:
                # Update existing call record with agent_id if needed
                if agent_id and not existing_call.agent_id:
                    await with_worker_db(
                        lambda db: crud_sip_calls.update(
                            db=db,
                            id=existing_call.id,
                            object={"agent_id": agent_id}
                        )
                    )
                    logger.info(f"Updated SIP call {call_id} with agent_id {agent_id}")
                
                # Mark call as active if it was just initiated
                if existing_call.status == SIPCallStatus.INITIATED.value:
                    await with_worker_db(
                        lambda db: crud_sip_calls.mark_call_answered(
                            db=db, 
                            call_id=call_id,
                            agent_id=agent_id
                        )
                    )
                    logger.info(f"Marked SIP call {call_id} as answered")
        except Exception as e:
            logger.error(f"Error recording/updating SIP call: {e}")
    
    return agent_id, call_metadata


def create_dynamic_function(tool, execution_handler):
    """Create a dynamic function with parameters matching the schema"""
    param_schema = tool.parameter_schema
    param_properties = param_schema.get("properties", {})
    required_params = param_schema.get("required", [])
    
    # Build parameter signature 
    param_names = list(param_properties.keys())
    param_defaults = {}
    param_annotations = {}
    
    # Create parameters with defaults for optional params
    for name in param_names:
        prop = param_properties.get(name, {})
        type_str = prop.get("type", "string")
        
        # Map JSON schema types to Python types
        if type_str == "string":
            param_annotations[name] = str
        elif type_str == "number":
            param_annotations[name] = float  
        elif type_str == "integer":
            param_annotations[name] = int
        elif type_str == "boolean":
            param_annotations[name] = bool
        else:
            param_annotations[name] = str
            
        # Set default for optional parameters
        if name not in required_params:
            param_defaults[name] = None
    
    # Define the function with closure around tool_id
    async def execute(*args, **kwargs):
        # Convert positional args to kwargs based on param_names
        for i, arg in enumerate(args):
            if i < len(param_names):
                kwargs[param_names[i]] = arg
                
        # Call the execution handler
        return await execution_handler(kwargs)
    
    # Add metadata to function
    execute.__name__ = tool.function_name
    execute.__doc__ = tool.function_description
    execute.__annotations__ = param_annotations
    
    # Create signature with explicit parameters
    parameters = []
    for param_name in param_names:
        if param_name in param_defaults:
            # Optional parameter with default
            param = inspect.Parameter(
                param_name, 
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=param_defaults[param_name],
                annotation=param_annotations.get(param_name)
            )
        else:
            # Required parameter
            param = inspect.Parameter(
                param_name, 
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=param_annotations.get(param_name)
            )
        parameters.append(param)
    
    # Set the signature on the function
    execute.__signature__ = inspect.Signature(parameters)
    
    return execute


async def setup_agent_with_profile(
    ctx: JobContext,
    participant: rtc.RemoteParticipant,
    agent_id: Optional[uuid.UUID] = None,
) -> Tuple[VoicePipelineAgent, Dict[str, Any]]:
    """
    Set up a voice agent with a profile for a participant.
    
    Args:
        ctx: The job context
        participant: The participant to interact with
        agent_id: UUID of the agent profile to use
        
    Returns:
        Tuple of (agent, resources_dict)
    """
    default_config = {
        "name": "Default Assistant",
        "description": "Default voice assistant configuration",
        "system_prompt": "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                         "You should use short and concise responses, and avoiding usage of unpronounceable punctuation.",
        "greeting": "Hey, how can I help you today?",
        "llm_provider": "openai",
        "tts_provider": "openai",
        "stt_provider": "deepgram",
        "llm_options": {"model": "gpt-4o", "temperature": 0.7},
        "tts_options": {"voice": "alloy", "speed": 1.0},
        "stt_options": {"model": "nova-3-general", "model_telephony": "nova-2-phonecall"},
        "allow_interruptions": True,
        "interrupt_speech_duration": 0.5,
        "interrupt_min_words": 0,
        "min_endpointing_delay": 0.5,
        "max_endpointing_delay": 6.0,
        "active": True,
        "is_default": True,
        "max_nested_function_calls": 1,
        "profile_options": {
            "enable_functions": True,
            "background_audio": {
                "enabled": False,
                "file": "office-ambience.mp3",
                "volume": 0.3,
                "loop": True
            }
        }
    }
    
    profile_config = default_config.copy()
    
    # Track resources for cleanup
    resources = {
        "local_participant": ctx.room.local_participant  # Store for cleanup access
    }
    
    # Check if this is a SIP participant
    is_sip_call = participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
    sip_metadata = {}
    
    # If agent_id is provided, try to get the agent profile from the database
    if agent_id is not None:
        try:
            # Use our worker-specific database helper
            profile = await with_worker_db(
                lambda db: crud_agent_profiles.get(db=db, id=agent_id)
            )
            
            if profile:
                logger.info(f"Found agent profile with ID {agent_id}: {profile.name}")
                # Convert profile to dictionary to match expected format
                profile_config = profile.model_dump()
            else:
                logger.warning(f"Agent profile with ID {agent_id} not found, using default configuration")
        except Exception as e:
            logger.error(f"Error retrieving agent profile: {e}")
    else:
        # If no agent ID was provided, try to get the default profile
        try:
            default_profile = await with_worker_db(
                lambda db: crud_agent_profiles.get_default(db=db)
            )
            if default_profile:
                logger.info(f"Using default agent profile: {default_profile.name}")
                profile_config = default_profile.model_dump()
                agent_id = default_profile.id
        except Exception as e:
            logger.error(f"Error retrieving default agent profile: {e}")
        
        if not agent_id:
            logger.info("No agent ID provided, using default configuration")
    
    # Enhance the configuration for SIP calls
    if is_sip_call:
        try:
            # Get SIP information
            sip_agent_id, sip_metadata = await get_sip_information(
                room_id=uuid.UUID(ctx.room.name) if ctx.room.name else None,
                participant=participant
            )
            
            # Override agent_id if SIP-specific agent is found
            if sip_agent_id:
                agent_id = sip_agent_id
                # Try to load the SIP-specific agent profile
                sip_profile = await with_worker_db(
                    lambda db: crud_agent_profiles.get(db=db, id=agent_id)
                )
                if sip_profile:
                    profile_config = sip_profile.model_dump()
                    logger.info(f"Using SIP-specific agent profile: {sip_profile.name}")
            
            # Store SIP metadata in resources for future use
            resources["sip_metadata"] = sip_metadata
            
            # Always enhance the profile for SIP calls
            profile_config = enhance_profile_for_sip_call(profile_config, participant, sip_metadata)
        except Exception as e:
            logger.error(f"Error processing SIP participant: {e}")
    
    # Define the RAG callback function
    def rag_callback(a, chat_ctx):
        return rag_service.enrich_with_rag(
            agent=a,
            chat_ctx=chat_ctx,
            agent_id=agent_id
        )
    
    fnc_ctx = None

    if profile_config.get('profile_options', {}).get("enable_functions", True) and agent_id is not None:
        try:
            # Fetch function tools assigned to this agent
            function_tools = await with_worker_db(
                lambda db: crud_function_tools.get_agent_functions(db=db, agent_id=agent_id)
            )
            
            if function_tools and len(function_tools) > 0:
                logger.info(f"Found {len(function_tools)} function tools for agent {agent_id}")
                
                # Create a function context
                fnc_ctx = FunctionContext()
                
                # Register each function tool with the context
                for tool in function_tools:
                    # Create an execution handler
                    async def execution_handler(tool_id):
                        async def handler(params):
                            result = await function_executor.execute_function(
                                function_id=tool_id,
                                parameters=params
                            )
                            
                            if not result["success"]:
                                raise Exception(result.get("error", "Unknown error"))
                                
                            return result["result"]
                        return handler
                    
                    # Create dynamic function with explicit parameters (not **kwargs)
                    execute_tool = create_dynamic_function(
                        tool, 
                        await execution_handler(tool.id)
                    )
                    
                    # Register with the Function Context
                    fnc_ctx.ai_callable(
                        name=tool.function_name,
                        description=tool.function_description
                    )(execute_tool)
                
                logger.info(f"Successfully registered {len(fnc_ctx.ai_functions)} functions with agent")
            else:
                logger.info(f"No function tools found for agent {agent_id}")
        except Exception as e:
            logger.error(f"Error setting up function tools: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.info(f"Function calling is disabled for agent {agent_id}")
    
    # Create the agent with the configuration
    agent = await create_voice_agent(
        ctx=ctx,
        vad=ctx.proc.userdata["vad"],
        profile_config=profile_config,
        func_ctx=fnc_ctx,
        before_llm_cb=rag_callback
    )

    # Start the agent
    agent.start(ctx.room, participant)
    
    # Store agent in resources for traceability
    resources["agent"] = agent
    
    # Set up background audio if enabled in profile
    background_audio_config = profile_config.get('profile_options', {}).get('background_audio', {})
    
    if background_audio_config.get('enabled', False):
        try:
            from .background_audio_source import BackgroundAudioSource, find_audio_file
            
            # Find the audio file
            audio_file = background_audio_config.get("file", "office-ambience.mp3")
            volume = float(background_audio_config.get("volume", 0.3))
            loop = bool(background_audio_config.get("loop", True))
            
            # Find the full path to the audio file
            full_audio_path = find_audio_file(audio_file)
            if not full_audio_path:
                logger.warning(f"Background audio file not found: {audio_file}")
            else:
                logger.info(f"Found background audio file: {full_audio_path}")
                
                # Create background audio source
                background_source = BackgroundAudioSource(
                    file_path=full_audio_path,
                    volume=volume,
                    loop=loop
                )
                
                # Start and get the audio track
                background_track = await background_source.start()
                
                if background_track:
                    # Publish the track
                    options = rtc.TrackPublishOptions()
                    options.source = rtc.TrackSource.SOURCE_MICROPHONE
                    
                    # Publish the track
                    background_publication = await ctx.room.local_participant.publish_track(
                        background_track, options
                    )
                    
                    # Store for cleanup
                    resources["background_audio"] = background_source
                    resources["background_publication"] = background_publication
                    resources["background_track"] = background_track
                    
                    logger.info(f"Published background audio track with SID: {background_publication.sid}")
                
        except ImportError as e:
            logger.error(f"Failed to import background audio module: {e}")
        except Exception as e:
            logger.error(f"Failed to start background audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Greet the user
    greeting = profile_config.get("greeting")
    if greeting:
        try:
            await agent.say(greeting, allow_interruptions=profile_config.get("allow_interruptions", True))
        except Exception as e:
            logger.error(f"Error delivering greeting: {e}")
    
    # Return both the agent and resources
    return agent, resources

def enhance_profile_for_sip_call(profile_config, participant, sip_metadata=None):
    """Enhance agent configuration for SIP calls with telephony-specific settings."""
    # Use telephony-optimized STT model if available
    stt_options = profile_config.get("stt_options", {})
    if stt_options and "model_telephony" in stt_options:
        stt_options["model"] = stt_options["model_telephony"]
        profile_config["stt_options"] = stt_options
    
    # Adjust system prompt for phone calls
    call_direction = sip_metadata.get("call_direction", "inbound") if sip_metadata else "inbound"
    original_prompt = profile_config.get("system_prompt", "")
    
    phone_prompt = (
        "You are speaking to someone on a phone call. "
        "Keep your responses clear, concise, and appropriate for a phone conversation. "
        "The person may not be able to see any visuals, so avoid referring to visuals or links. "
        "Speak in short sentences and use simple language."
    )
    
    # Add phone number information if available
    phone_number = None
    if sip_metadata and "phone_number" in sip_metadata:
        phone_number = sip_metadata["phone_number"]
    elif participant.attributes.get("sip.phoneNumber"):
        phone_number = participant.attributes.get("sip.phoneNumber")
    elif participant.attributes.get("sip.trunkPhoneNumber"):
        phone_number = participant.attributes.get("sip.trunkPhoneNumber")
    
    if phone_number:
        phone_prompt += f"\nThe caller's phone number is {phone_number}."
    
    # Add SIP-specific context
    if sip_metadata and "sip_trunkID" in sip_metadata:
        phone_prompt += f"\nThis call is coming through SIP trunk {sip_metadata['sip_trunkID']}."
    
    profile_config["system_prompt"] = phone_prompt + "\n\n" + original_prompt
    
    # Adjust greeting based on call direction
    if call_direction == "inbound":
        profile_config["greeting"] = "Hello, thanks for calling. How can I help you today?"
    else:
        profile_config["greeting"] = "Hello, I'm calling from LiveKit. How are you today?"
    
    # Optimize agent behavior for telephony
    profile_config["allow_interruptions"] = True
    profile_config["interrupt_speech_duration"] = 0.3  # Lower threshold for SIP calls
    profile_config["min_endpointing_delay"] = 0.3  # Quicker responses for SIP
    profile_config["max_endpointing_delay"] = 3.0  # Shorter maximum delay for phone calls
    
    # Tune TTS settings for telephony clarity
    if profile_config.get("tts_provider") == "openai":
        tts_options = profile_config.get("tts_options", {})
        # Use a slower speed for better comprehension
        tts_options["speed"] = 0.95
        profile_config["tts_options"] = tts_options
    elif profile_config.get("tts_provider") == "google":
        tts_options = profile_config.get("tts_options", {})
        # Adjust speaking rate for Google TTS
        tts_options["speaking_rate"] = 0.95
        # Slightly lower pitch for better clarity on phone lines
        tts_options["pitch"] = -0.2
        profile_config["tts_options"] = tts_options
    
    return profile_config

async def cleanup_agent_resources(agent, resources=None):
    """
    Clean up all resources associated with an agent.
    
    Args:
        agent: The VoicePipelineAgent instance to clean up
        resources: Dictionary of additional resources to clean up
    """
    if not agent:
        return
        
    logger.info("Cleaning up agent resources")
    
    # Stop the agent
    try:
        # Interrupt any ongoing speech first
        agent.interrupt(interrupt_all=True)
        
        # Close the agent
        await agent.aclose()
        logger.info("Agent closed successfully")
    except Exception as e:
        logger.error(f"Error closing agent: {e}")
    
    # Clean up background audio and other resources
    if resources:
        if "background_audio" in resources and resources["background_audio"]:
            try:
                background_audio = resources["background_audio"]
                await background_audio.stop()
                logger.info("Background audio stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping background audio: {e}")
        
        # Unpublish background audio track if necessary
        if "background_publication" in resources and resources["background_publication"]:
            try:
                publication = resources["background_publication"]
                # Try to unpublish the track
                try:
                    # First mute to minimize any disruption
                    await publication.track.mute()
                    logger.info("Background audio track muted before cleanup")
                    
                    # Try to unpublish if we can
                    lp = resources.get("local_participant")
                    if lp and hasattr(lp, "unpublish_track"):
                        await lp.unpublish_track(publication.sid)
                        logger.info(f"Unpublished background audio track {publication.sid}")
                except Exception as e:
                    logger.error(f"Error unpublishing background track: {e}")
            except Exception as e:
                logger.error(f"Error handling background audio publication: {e}")
                
        # Clean up any other resource types
        for resource_type, resource in resources.items():
            if resource_type not in ["background_audio", "background_publication", "local_participant"]:
                try:
                    if hasattr(resource, "aclose") and callable(resource.aclose):
                        await resource.aclose()
                    elif hasattr(resource, "close") and callable(resource.close):
                        resource.close()
                    logger.info(f"Resource {resource_type} cleaned up successfully")
                except Exception as e:
                    logger.error(f"Error cleaning up resource {resource_type}: {e}")