import asyncio
import logging
import uuid

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent

from ..services.agent_profile import setup_agent_with_profile, cleanup_agent_resources
from ..crud.crud_agent_reference import crud_agent_references
from ..utils.db_utils import with_worker_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveKit Worker")

def prewarm(proc: JobProcess):
    """Initialize components that can be reused across jobs."""
    # Load and store VAD model in process userdata
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("Voice agent prewarm complete: VAD model loaded")

async def entrypoint(ctx: JobContext):
    """Main entry point for voice agent jobs."""
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Check for agent ID in the reference table based on room name
    agent_id = None
    active_agents = {}  # Track active agents by participant ID
    background_resources = {}  # Track background resources
    usage_collectors = {}
    
    # Try to parse the room name as a UUID and look up the agent_id in the reference table
    try:
        room_name = ctx.room.name
        try:
            # Parse the room name as UUID
            room_uuid = uuid.UUID(room_name)
            logger.info(f"Room name {room_name} is a valid UUID")
            
            # Use our worker-specific database helper
            reference = await with_worker_db(
                lambda db: crud_agent_references.get(
                    db=db, roomid=room_uuid
                )
            )
            
            if reference:
                agent_id = reference["agentid"]
                logger.info(f"Found agent ID {agent_id} in reference table for room {room_name}")
            else:
                logger.warning(f"No agent reference found for room {room_name}")
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Room name {room_name} is not a valid UUID: {e}")
    except Exception as e:
        logger.warning(f"Error checking reference table: {e}")
    
    # Set up participant event handlers
    async def handle_participant(participant):
        logger.info(f"Starting voice assistant for participant {participant.identity}")
        
        # Create and start the agent with the agent_id
        logger.info(f"Using agent with ID: {agent_id}")
        agent, resources = await setup_agent_with_profile(
            ctx=ctx, 
            participant=participant,
            agent_id=agent_id
        )
        
        # Store agent and resources for cleanup
        active_agents[participant.identity] = agent
        background_resources[participant.identity] = resources
        
        # Set up metrics collection
        usage_collector = metrics.UsageCollector()
        usage_collectors[participant.identity] = usage_collector

        @agent.on("metrics_collected")
        def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
            metrics.log_metrics(mtrcs)
            usage_collector.collect(mtrcs)

        return agent, usage_collector
    
    # Define async cleanup functions
    async def cleanup_participant_resources(participant):
        logger.info(f"Participant {participant.identity} disconnected, cleaning up resources")
        if participant.identity in active_agents:
            agent = active_agents[participant.identity]
            resources = background_resources.get(participant.identity, {})
            
            try:
                # Clean up agent resources
                await cleanup_agent_resources(agent, resources)
                logger.info(f"Agent resources for {participant.identity} cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up agent resources: {e}")
            
            # Remove from tracking dictionaries
            del active_agents[participant.identity]
            if participant.identity in background_resources:
                del background_resources[participant.identity]
    
    async def cleanup_room_resources(reason):
        logger.info(f"Room disconnected with reason: {reason}")
        # Clean up all active agents
        for participant_id, agent in list(active_agents.items()):
            resources = background_resources.get(participant_id, {})
            try:
                await cleanup_agent_resources(agent, resources)
                logger.info(f"Cleaned up agent for {participant_id} during room disconnection")
            except Exception as e:
                logger.error(f"Error cleaning up agent during room disconnect: {e}")
    
    # Use synchronous callbacks that create async tasks
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        logger.info(f"Participant disconnect event received for {participant.identity}")
        asyncio.create_task(cleanup_participant_resources(participant))
    
    @ctx.room.on("disconnected")
    def on_room_disconnected(reason):
        logger.info(f"Room disconnect event received: {reason}")
        asyncio.create_task(cleanup_room_resources(reason))
    
    # Register global shutdown callback
    async def shutdown_callback(reason=""):
        logger.info(f"Job shutting down: {reason}")
        # Clean up all resources
        for participant_id, agent in list(active_agents.items()):
            resources = background_resources.get(participant_id, {})
            try:
                await cleanup_agent_resources(agent, resources)
                # Log final usage
                collector = usage_collectors.get(participant_id)
                if collector:
                    summary = collector.get_summary()
                    logger.info(f"Usage for {participant_id}: {summary}")
            except Exception as e:
                logger.error(f"Error during shutdown cleanup: {e}")
    
    ctx.add_shutdown_callback(shutdown_callback)
    
    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    await handle_participant(participant)
    
    # Set up handler for future participants (using the entrypoint approach)
    ctx.add_participant_entrypoint(handle_participant)