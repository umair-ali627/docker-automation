import numpy as np
from livekit import rtc
import logging

logger = logging.getLogger("audio-utils")

def create_audio_frame_from_numpy(
    samples: np.ndarray, 
    sample_rate: int, 
    channels: int
) -> rtc.AudioFrame:
    """
    Create a LiveKit AudioFrame from a numpy array of audio samples.
    
    Args:
        samples: Numpy array of audio samples (int16)
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        
    Returns:
        rtc.AudioFrame: A LiveKit AudioFrame object
    """
    if not isinstance(samples, np.ndarray):
        raise TypeError("samples must be a numpy array")
        
    # Ensure samples are int16
    if samples.dtype != np.int16:
        logger.warning(f"Converting samples from {samples.dtype} to int16")
        samples = samples.astype(np.int16)
    
    # Convert to bytes
    samples_bytes = samples.tobytes()
    
    # Calculate samples per channel
    samples_per_channel = len(samples) // channels
    
    # Create AudioFrame
    audio_frame = rtc.AudioFrame(
        data=samples_bytes,
        sample_rate=sample_rate,
        num_channels=channels,
        samples_per_channel=samples_per_channel
    )
    
    return audio_frame