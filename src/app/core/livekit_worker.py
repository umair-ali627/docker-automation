import asyncio
import logging
from typing import Optional

from livekit.agents import JobProcess, Worker, WorkerOptions
from ..core.config import settings

logger = logging.getLogger("livekit-worker")

# Global worker process and worker
worker_process: Optional[JobProcess] = None
worker: Optional[Worker] = None

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
    
    return f"wss://{url}"

async def initialize_worker() -> None:
    """Initialize the LiveKit worker process."""
    global worker_process, worker
    
    # Import your worker configuration module
    from ..workers.voice_agent import entrypoint, prewarm
    
    logger.info("Initializing LiveKit worker...")
    
    # Initialize worker with the configured options
    options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        ws_url=normalize_livekit_url(settings.LIVEKIT_HOST),
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
        # Set agent_name to empty and specify other options for automatic dispatch
        agent_name="",  # Empty string means automatic dispatch
        job_memory_warn_mb=500,  # Empty string means automatic dispatch
        job_memory_limit_mb=1024,
    )
    
    
    # Create the worker process and worker
    worker_process = JobProcess(user_arguments=None)
    worker = Worker(options, devmode=True, loop=asyncio.get_event_loop())
    
    # Prewarm the worker to initialize components that can be reused
    if prewarm:
        prewarm(worker_process)
    
    logger.info("LiveKit worker initialized successfully")

async def start_worker() -> None:
    """Start the LiveKit worker to begin processing jobs."""
    global worker, worker_process
    
    if worker is None:
        logger.error("Cannot start worker: worker not initialized")
        return
    
    logger.info("Starting LiveKit worker...")
    
    # Start the worker in the background
    asyncio.create_task(worker.run())
    
    logger.info("LiveKit worker started successfully")

async def shutdown_worker() -> None:
    """Shutdown the LiveKit worker gracefully."""
    global worker, worker_process
    
    if worker is None:
        return
    
    logger.info("Shutting down LiveKit worker...")
    
    # Gracefully shut down the worker
    try:
        # First drain any active jobs
        await worker.drain(timeout=5.0)
        
        # Then close the worker
        await asyncio.wait_for(worker.aclose(), timeout=5.0)
        worker = None
        worker_process = None
        logger.info("LiveKit worker shut down successfully")
    except asyncio.TimeoutError:
        logger.warning("LiveKit worker shutdown timed out, forcing close")
        worker = None
        worker_process = None