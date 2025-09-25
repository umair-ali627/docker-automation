import asyncio
import logging
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

# Configure logging
logger = logging.getLogger("voice-assistant")


def prewarm(proc: JobProcess):
    """Initialize any resources that should be preloaded and cached."""
    # Cache the VAD model to avoid loading it repeatedly
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent."""
    # Access the global worker instance for heartbeat updates
    worker = LiveKitAgentWorker()
    
    # Log that the entrypoint function is executing
    logger.info("LiveKit agent entrypoint function started")
    worker.heartbeat()
    
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by our company. Your interface with users will be voice. "
            "You should use short and concise responses, and avoid usage of unpronounceable punctuation. "
            "Answer politely to user questions."
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    worker.heartbeat()

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")
    worker.heartbeat()

    # Select appropriate model based on connection type
    dg_model = "nova-3-general"
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        # Use a model optimized for telephony
        dg_model = "nova-2-phonecall"

    # Create the voice agent pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model=dg_model),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
    )

    # Start the agent with the current room and participant
    agent.start(ctx.room, participant)
    worker.heartbeat()
    logger.info("Voice pipeline agent started successfully")

    # Track and log usage metrics
    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)
        usage_collector.collect(mtrcs)
        # Use heartbeat to confirm the agent is still processing events
        worker.heartbeat()

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)
    
    # Set up a periodic heartbeat task
    async def heartbeat_task():
        while True:
            try:
                worker.heartbeat()
                logger.debug("LiveKit agent heartbeat")
                await asyncio.sleep(60)  # Heartbeat every minute
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(60)  # Continue even if there's an error
    
    # Start the heartbeat task
    asyncio.create_task(heartbeat_task())

    # Handle chat messages (optional)
    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = agent.llm.chat(chat_ctx=chat_ctx)
        await agent.say(stream)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))
            worker.heartbeat()  # Record activity

    # Greet the user
    await agent.say("Hello, how can I help you today?", allow_interruptions=True)
    worker.heartbeat()


class LiveKitAgentWorker:
    """Manages the LiveKit agent worker process."""
    
    _instance = None
    _worker_process = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveKitAgentWorker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        load_dotenv()  # Load environment variables from .env file
        self._initialized = True
        self._running = False
        self._worker_start_time = None
        self._heartbeat_count = 0
        self._last_heartbeat = None
        
    def start(self):
        """Start the LiveKit agent worker process."""
        if self._worker_process:
            logger.warning("Worker process already running")
            return
            
        logger.info("Starting LiveKit agent worker")
        
        worker_options = WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
        
        # Start the worker process in a separate thread to avoid blocking the main thread
        import threading
        import time
        
        self._running = False
        self._worker_start_time = time.time()
        
        def run_worker():
            try:
                logger.info("LiveKit worker thread starting")
                self._running = True
                self._worker_process = cli.run_app(worker_options)
            except Exception as e:
                self._running = False
                logger.error(f"Error running LiveKit agent worker: {e}")
        
        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()
        
        # Give the worker a moment to initialize
        time.sleep(1)
        
        if self._running:
            logger.info(f"LiveKit agent worker started successfully at {time.ctime(self._worker_start_time)}")
        else:
            logger.warning("LiveKit agent worker may not have started properly")
        
    def stop(self):
        """Stop the LiveKit agent worker process."""
        if self._worker_process:
            logger.info("Stopping LiveKit agent worker")
            # Implement proper shutdown based on how the process was started
            # This may involve sending signals or calling a shutdown method
            self._worker_process = None
            self._running = False
            self._worker_start_time = None
            logger.info("LiveKit agent worker stopped")
            
    def is_running(self):
        """Check if the worker is running."""
        return self._running
        
    def get_status(self):
        """Get detailed status information about the worker."""
        import time
        
        if not self._running:
            return {
                "status": "stopped",
                "running": False,
                "message": "Worker is not running"
            }
            
        uptime = time.time() - self._worker_start_time if self._worker_start_time else 0
        
        return {
            "status": "running",
            "running": True,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "start_time": time.ctime(self._worker_start_time) if self._worker_start_time else None,
            "heartbeat_count": self._heartbeat_count,
            "last_heartbeat": self._last_heartbeat
        }
    
    def _format_uptime(self, seconds):
        """Format seconds into a readable uptime string."""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not parts:
            parts.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts)
        
    def heartbeat(self):
        """Register a heartbeat from the worker to confirm it's still functioning."""
        import time
        self._heartbeat_count += 1
        self._last_heartbeat = time.ctime()
        return self._heartbeat_count