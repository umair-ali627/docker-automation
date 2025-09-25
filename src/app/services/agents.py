import logging
import asyncio
import uuid
from typing import Dict, Optional, Any, List

from dotenv import load_dotenv
from livekit import rtc, api
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    llm,
    metrics,
)
# from livekit.agents.pipeline import VoicePipelineAgent
# from livekit.plugins import silero, deepgram, openai


from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
# from livekit.plugins.turn_detector.multilingual import MultilingualModel


from ..core.config import settings

logger = logging.getLogger("voice-assistant")


def normalize_livekit_url(url: str) -> str:
    """
    Normalize a LiveKit URL to ensure proper protocol prefix
    """
    # Strip any existing protocol
    if url.startswith(("wss://", "ws://", "https://", "http://")):
        if url.startswith("wss://"):
            return url  # Already in correct format
        elif url.startswith("ws://"):
            parts = url[5:]
            return f"wss://{parts}"
        elif url.startswith("https://"):
            parts = url[8:]
            return f"wss://{parts}"
        elif url.startswith("http://"):
            parts = url[7:]
            return f"wss://{parts}"

    # No protocol, add wss://
    return f"wss://{url}"


class AgentMetrics:
    """Tracks metrics for an agent"""

    def __init__(self):
        self.created_at = asyncio.get_event_loop().time()
        self.total_audio_processed = 0
        self.total_requests = 0
        self.active_connections = 0
        self.error_count = 0

    def to_dict(self):
        now = asyncio.get_event_loop().time()
        uptime = now - self.created_at
        return {
            "uptime_seconds": round(uptime, 2),
            "total_audio_processed_bytes": self.total_audio_processed,
            "total_requests": self.total_requests,
            "active_connections": self.active_connections,
            "error_count": self.error_count
        }


class AgentRunner:
    """Manages a single agent instance for a LiveKit room"""

    def __init__(self, agent_id: str, room_name: str):
        self.agent_id = agent_id
        self.room_name = room_name
        self.agent: Optional[AgentSession] = None
        self.room: Optional[rtc.Room] = None
        self.metrics = AgentMetrics()
        self.usage_collector = metrics.UsageCollector()
        self.task: Optional[asyncio.Task] = None

    async def _wait_for_participant(self, room: rtc.Room, timeout: int = 120) -> rtc.Participant:
        """Wait for a participant to join the room with improved logging"""
        logger.info(
            f"Waiting for participants to join room {self.room_name} (timeout: {timeout}s)")

        # Check if there are already participants in the room
        participants = list(room.remote_participants.values())
        if participants:
            logger.info(
                f"Found existing participant: {participants[0].identity}")
            return participants[0]

        # Set up a participant connected listener with an event
        participant_joined = asyncio.Event()
        participant_identity = None

        def on_participant_connected(participant):
            nonlocal participant_identity
            logger.info(f"New participant connected: {participant.identity}")
            participant_identity = participant.identity
            participant_joined.set()

        # Add the listener
        room.on("participant_connected", on_participant_connected)

        try:
            # Wait for the event with timeout
            start_time = asyncio.get_event_loop().time()
            while not participant_joined.is_set():
                try:
                    # Check every 10 seconds
                    await asyncio.wait_for(participant_joined.wait(), timeout=10)
                except asyncio.TimeoutError:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(
                            "No participants joined the room within the timeout period")
                    logger.info(
                        f"Still waiting for participants... ({int(elapsed)}s elapsed)")

                    # Log room connection state for debugging
                    logger.info(
                        f"Room connection state: {room.connection_state}")
                    logger.info(
                        f"Current participants count: {len(room.remote_participants)}")

            # Get the participant object
            return room.remote_participants[participant_identity]
        finally:
            # Clean up the listener
            room.off("participant_connected", on_participant_connected)

    async def start(self, token: str, system_prompt: str = None):
        """Start the agent in a room"""
        if self.task:
            logger.warning(
                f"Agent {self.agent_id} already running for room {self.room_name}")
            return

        # Start the agent in a background task
        self.task = asyncio.create_task(
            self._agent_entrypoint(token, system_prompt)
        )

    async def stop(self):
        """Stop the agent and disconnect from the room"""
        if self.room:
            try:
                await self.room.disconnect()
                self.room = None
            except Exception as e:
                logger.exception(f"Error disconnecting from room: {e}")

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        # Log final usage metrics
        summary = self.usage_collector.get_summary()
        logger.info(f"Usage for agent {self.agent_id}: {summary}")

    async def _agent_entrypoint(self, token: str, system_prompt: str = None):
        """Agent entrypoint function - similar to what would be passed to WorkerOptions"""
        try:
            # Default system prompt if none provided
            if not system_prompt:
                system_prompt = (
                    "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                    "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
                )

            # Create initial chat context
            initial_ctx = llm.ChatContext().append(
                role="system",
                text=system_prompt,
            )

            # Get properly formatted LiveKit server URL
            livekit_host = settings.LIVEKIT_HOST
            livekit_url = normalize_livekit_url(livekit_host)

            logger.info(
                f"Connecting to room {self.room_name} on {livekit_url}")

            # Connect to the room
            from livekit.rtc.room import RoomOptions
            room_options = RoomOptions()
            room_options.auto_subscribe = True  # Make sure this is True, not just 1
            logger.info(
                f"Room options auto_subscribe: {room_options.auto_subscribe}")
            # Use the integer value 1 for auto-subscribing to audio only
            # 0: NONE, 1: AUDIO_ONLY, 2: ALL
            room_options.auto_subscribe = 1  # Equivalent to AUDIO_ONLY
            self.room = rtc.Room()
            await self.room.connect(livekit_url, token, options=room_options)

            @self.room.on("track_subscribed")
            def on_track_subscribed(track, publication, participant):
                logger.info(
                    f"Track subscribed: {track.kind} from {participant.identity}")

                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info(
                        f"Audio track from {participant.identity} is now available")
        # Add any additional debugging you want here

            @self.room.on("track_unsubscribed")
            def on_track_unsubscribed(track, publication, participant):
                logger.info(
                    f"Track unsubscribed from {participant.identity}: {track.kind}")

            # Wait for the first participant to connect
            # After waiting for participant
            participant = await self._wait_for_participant(self.room)
            logger.info(
                f"Starting voice assistant for participant {participant.identity}")
            logger.info(f"Participant info: {participant}")
            logger.info(
                f"Participant has tracks: {len(participant.track_publications)}")

            # List any tracks the participant already has
            for track_sid, publication in participant.track_publications.items():
                logger.info(
                    f"Participant track: {publication.kind}, track present: {publication.track is not None}")
                if publication.track:
                    logger.info(
                        f"Track type: {type(publication.track).__name__}")

            # Choose the appropriate model based on participant type
            dg_model = "nova-3-general"
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                # Use a model optimized for telephony
                dg_model = "nova-2-phonecall"

            # Add after creating the VAD instance
            vad_instance = silero.VAD.load()

            # Test the VAD with a simple audio sample
            # This will help confirm if VAD is functional
            logger.info(f"VAD loaded: {vad_instance}")

            # Create the agent using AgentSession pattern
            self.agent = AgentSession(
                vad=silero.VAD.load(),
                stt=deepgram.STT(
                    model=dg_model, api_key=settings.DEEPGRAM_API_KEY),
                llm=openai.LLM(api_key=settings.OPENAI_API_KEY),
                tts=openai.TTS(api_key=settings.OPENAI_API_KEY),
                chat_ctx=initial_ctx,
                allow_interruptions=True,
            )

            # Debug the agent
            logger.info(f"Agent created, VAD: {self.agent._vad}")
            logger.info(f"Agent created, STT: {self.agent._stt}")

            # Add more detailed event handlers with correct parameter handling
            @self.agent.on("user_started_speaking")
            def on_user_speaking():
                logger.info("User started speaking")

            @self.agent.on("user_stopped_speaking")
            def on_user_stopped_speaking():
                logger.info("User stopped speaking")

            # Note: These handlers need to accept the event parameter
            @self.agent.on("interim_transcript")
            def on_interim_transcript(event):
                logger.info(
                    f"Interim transcript: {event.alternatives[0].text}")

            @self.agent.on("final_transcript")
            def on_final_transcript(event):
                logger.info(f"Final transcript: {event.alternatives[0].text}")

            # Start the agent
            logger.info("Starting the agent...")
            self.agent.start(self.room, participant)
            logger.info("Agent started")

            # Add a short delay to ensure initialization completes
            await asyncio.sleep(1)

            # Check human input initialization
            if self.agent._human_input:
                logger.info("Human input is initialized")
                logger.info(f"Human input VAD: {self.agent._human_input._vad}")
                logger.info(f"Human input STT: {self.agent._human_input._stt}")
                logger.info(
                    f"Human input participant: {self.agent._human_input._participant.identity}")

                # Check if VAD has event handlers
                vad_handlers = getattr(
                    self.agent._human_input._vad, '_event_handlers', {})
                logger.info(f"VAD has {len(vad_handlers)} event handlers")
            else:
                logger.error(
                    "Human input is NOT initialized - this is a problem")

            # Listen to incoming chat messages
            chat = rtc.ChatManager(self.room)

            @chat.on("message_received")
            def on_chat_received(msg: rtc.ChatMessage):
                if msg.message:
                    asyncio.create_task(self._answer_from_text(msg.message))

            # Welcome message
            await self.agent.say("Hey, how can I help you today?", allow_interruptions=True)

            # Keep the task running until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info(f"Agent task for room {self.room_name} cancelled")
                raise

        except Exception as e:
            logger.exception(
                f"Error in agent entrypoint for room {self.room_name}: {e}")
            self.metrics.error_count += 1

    async def _wait_for_participant(self, room: rtc.Room, timeout: int = 60) -> rtc.Participant:
        """Wait for a participant to join the room"""
        for _ in range(timeout):
            # Fixed: Use remote_participants instead of participants
            participants = room.remote_participants
            if participants:
                return next(iter(participants.values()))
            await asyncio.sleep(1)
        raise TimeoutError(
            "No participants joined the room within the timeout period")

    async def _answer_from_text(self, text: str):
        """Process a text message and respond with voice"""
        if not self.agent:
            logger.warning("Agent not initialized, cannot process text")
            return

        chat_ctx = self.agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=text)
        stream = self.agent.llm.chat(chat_ctx=chat_ctx)
        await self.agent.say(stream)


class ScalableAgentService:
    """
    Scalable service to manage voice AI agents for different rooms
    """

    def __init__(self):
        self.agent_runners: Dict[str, AgentRunner] = {}
        self.room_to_agent_map: Dict[str, str] = {}

    async def create_agent_for_room(
        self,
        room_name: str,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """Create a new agent for a room"""
        # Check if an agent is already assigned to this room
        if room_name in self.room_to_agent_map:
            agent_id = self.room_to_agent_map[room_name]
            if agent_id in self.agent_runners:
                logger.info(
                    f"Using existing agent {agent_id} for room {room_name}")
                return {
                    "agent_id": agent_id,
                    "room_name": room_name,
                    "status": "created"
                }

        # Create a new agent
        logger.info(f"Creating new agent for room {room_name}")

        # Generate a unique ID for this agent
        agent_id = str(uuid.uuid4())

        # Create an agent runner
        runner = AgentRunner(agent_id, room_name)

        # Store the runner and track metrics
        self.agent_runners[agent_id] = runner
        self.room_to_agent_map[room_name] = agent_id

        # Return agent info
        return {
            "agent_id": agent_id,
            "room_name": room_name,
            "status": "created"
        }

    async def start_agent(self, room_name: str, token: str, system_prompt: str = None) -> Dict[str, Any]:
        """Start an agent in a room using the provided token"""
        if room_name not in self.room_to_agent_map:
            logger.warning(f"No agent found for room {room_name}")
            return {
                "status": "error",
                "message": "No agent found for this room"
            }

        agent_id = self.room_to_agent_map[room_name]
        runner = self.agent_runners[agent_id]

        try:
            # Start the agent
            await runner.start(token, system_prompt)

            return {
                "status": "started",
                "agent_id": agent_id,
                "room_name": room_name
            }

        except Exception as e:
            logger.exception(f"Error starting agent for room {room_name}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def stop_agent(self, room_name: str) -> bool:
        """Stop an agent and remove it from a room"""
        if room_name not in self.room_to_agent_map:
            logger.warning(f"No agent found for room {room_name}")
            return False

        agent_id = self.room_to_agent_map[room_name]
        if agent_id not in self.agent_runners:
            logger.warning(f"Agent {agent_id} not found")
            del self.room_to_agent_map[room_name]
            return False

        runner = self.agent_runners[agent_id]

        try:
            # Stop the agent
            await runner.stop()

            # Clean up references
            del self.room_to_agent_map[room_name]
            del self.agent_runners[agent_id]

            return True
        except Exception as e:
            logger.exception(f"Error stopping agent for room {room_name}: {e}")
            return False

    def get_agent_metrics(self, room_name: str = None) -> Dict:
        """
        Get metrics for a specific room's agent or all agents

        If room_name is specified, returns metrics for that room's agent.
        Otherwise, returns aggregated metrics for all agents.
        """
        if room_name:
            if room_name not in self.room_to_agent_map:
                return {}

            agent_id = self.room_to_agent_map[room_name]
            if agent_id not in self.agent_runners:
                return {}

            return self.agent_runners[agent_id].metrics.to_dict()

        # Aggregate metrics for all agents
        aggregate = {
            "total_agents": len(self.agent_runners),
            "active_rooms": sum(1 for runner in self.agent_runners.values() if runner.task is not None),
            "total_audio_processed": 0,
            "total_requests": 0,
            "active_connections": 0,
            "error_count": 0
        }

        for runner in self.agent_runners.values():
            aggregate["total_audio_processed"] += runner.metrics.total_audio_processed
            aggregate["total_requests"] += runner.metrics.total_requests
            aggregate["active_connections"] += runner.metrics.active_connections
            aggregate["error_count"] += runner.metrics.error_count

        return aggregate

    def list_rooms(self) -> List[Dict[str, Any]]:
        """List all rooms with their current status"""
        rooms = []
        for room_name, agent_id in self.room_to_agent_map.items():
            if agent_id in self.agent_runners:
                runner = self.agent_runners[agent_id]
                rooms.append({
                    "room_name": room_name,
                    "agent_id": agent_id,
                    "status": "active" if runner.task is not None else "created",
                    "metrics": runner.metrics.to_dict()
                })
        return rooms

    def generate_room_token(self, room_name: str, identity: str = "voice-ai-agent"):
        """Generate a token for joining a LiveKit room"""
        # Get API key and secret from environment variables
        api_key = settings.LIVEKIT_API_KEY
        api_secret = settings.LIVEKIT_API_SECRET

        if not api_key or not api_secret:
            raise ValueError(
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment variables")

        # Create an access token using the newer API approach
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(identity) \
            .with_name(identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )).to_jwt()

        return token


# Singleton instance
scalable_agent_service = ScalableAgentService()
