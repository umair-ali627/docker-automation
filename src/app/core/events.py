import logging
from typing import Callable

from fastapi import FastAPI

from ..services.livekit_agent import LiveKitAgentWorker

logger = logging.getLogger(__name__)


def create_start_app_handler(app: FastAPI) -> Callable:
    """Create a handler to run when the application starts."""

    async def start_app() -> None:
        """Initialize components when the application starts."""
        # Initialize and start the LiveKit agent worker
        try:
            logger.info("Attempting to initialize LiveKit worker...")
            worker = LiveKitAgentWorker()
            logger.info("LiveKit worker instance created, starting worker...")
            worker.start()
            logger.info("LiveKit worker start method completed")
            app.state.livekit_worker = worker
            logger.info("LiveKit worker successfully stored in app state")
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit agent worker: {e}", exc_info=True)
            # Re-raise the exception to see it in the console during development
            raise

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """Create a handler to run when the application stops."""

    async def stop_app() -> None:
        """Clean up resources when the application stops."""
        # Stop the LiveKit agent worker if it exists
        if hasattr(app.state, "livekit_worker"):
            try:
                app.state.livekit_worker.stop()
                logger.info("LiveKit agent worker stopped")
            except Exception as e:
                logger.error(f"Error stopping LiveKit agent worker: {e}")

    return stop_app