import asyncio
import logging
import os
import math
import numpy as np
from typing import Optional

from livekit import rtc

logger = logging.getLogger("background-audio")

class BackgroundAudioSource:
    """
    A streamlined class for playing background audio in LiveKit rooms.
    Loads an audio file, creates an audio source and track, and handles playback.
    """
    
    def __init__(
        self, 
        file_path: str,
        volume: float = 0.3,
        sample_rate: int = 48000,
        channels: int = 1,
        chunk_duration_ms: int = 20,
        loop: bool = True
    ):
        """
        Initialize the background audio source.
        
        Args:
            file_path: Path to the audio file
            volume: Volume level (0.0 to 1.0)
            sample_rate: Sample rate in Hz (default: 48000)
            channels: Number of audio channels (default: 1)
            chunk_duration_ms: Duration of each chunk in milliseconds (default: 20)
            loop: Whether to loop the audio (default: True)
        """
        self.file_path = file_path
        self.volume = max(0.0, min(1.0, volume))
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration_ms = chunk_duration_ms
        self.loop = loop
        
        # Calculate chunk size based on duration
        self.chunk_size = int((self.sample_rate * self.chunk_duration_ms) / 1000)
        
        self._audio_source = None
        self._track = None
        self._audio_data = None
        self._playback_task = None
        self._running = False
        
        logger.info(f"Initialized BackgroundAudioSource: {file_path}, volume: {volume}")
    
    async def load_audio(self) -> bool:
        """
        Load and prepare the audio file with memory optimizations.
        
        Returns:
            bool: True if audio was loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading audio from file: {self.file_path}")
            
            # Verify file exists
            if not os.path.exists(self.file_path):
                logger.error(f"Audio file not found: {self.file_path}")
                return await self._create_synthetic_audio()
            
            try:
                # Import here to avoid dependency issues if pydub isn't available
                from pydub import AudioSegment
                import math
                
                # Load the audio using pydub
                sound = AudioSegment.from_file(self.file_path)
                
                # Memory optimization: Downsample if high quality
                original_rate = sound.frame_rate
                original_channels = sound.channels
                
                if sound.channels > self.channels or sound.frame_rate > self.sample_rate:
                    logger.info(f"Downsampling audio from {original_rate}Hz {original_channels}ch to {self.sample_rate}Hz {self.channels}ch")
                
                # Convert to the desired format
                sound = sound.set_channels(self.channels)
                sound = sound.set_frame_rate(self.sample_rate)
                
                # Memory optimization: Limit duration if extremely long
                max_duration_sec = 60  # Limit to 60 seconds to save memory
                if len(sound) > max_duration_sec * 1000:  # pydub measures in milliseconds
                    logger.warning(f"Audio file is very long ({len(sound)/1000:.1f}s), trimming to {max_duration_sec}s")
                    sound = sound[:max_duration_sec * 1000]
                
                # Apply volume using apply_gain (volume in dB)
                # Convert from linear scale (0.0-1.0) to dB
                if self.volume < 1.0:
                    gain_db = 20 * (self.volume - 1)  # This gives a negative dB value
                    sound = sound.apply_gain(gain_db)
                elif self.volume > 1.0:
                    sound = sound.apply_gain(20 * math.log10(self.volume))
                
                # Convert to numpy array
                audio_array = np.array(sound.get_array_of_samples(), dtype=np.int16)
                
                # Store the processed audio data
                self._audio_data = audio_array
                # Save original for volume adjustments
                self._original_audio_data = audio_array.copy()
                
                # Memory optimization: Delete the sound object to free memory
                del sound
                
                logger.info(f"Audio loaded successfully: {len(audio_array)/self.sample_rate:.2f} seconds")
                return True
                    
            except Exception as e:
                logger.error(f"Error processing audio file {self.file_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return await self._create_synthetic_audio()
                    
        except Exception as e:
            logger.error(f"Error in audio loading process: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return await self._create_synthetic_audio()
    
    async def start(self) -> Optional[rtc.LocalAudioTrack]:
        """
        Start playing the background audio.
        
        Returns:
            rtc.LocalAudioTrack: The audio track that can be published, or None if failed
        """
        try:
            # Load audio if not already loaded
            if self._audio_data is None:
                success = await self.load_audio()
                if not success:
                    logger.error("Failed to load audio data")
                    return None
            
            # Create audio source
            self._audio_source = rtc.AudioSource(
                sample_rate=self.sample_rate, 
                num_channels=self.channels,
                queue_size_ms=2000
            )
            
            # Create audio track
            self._track = rtc.LocalAudioTrack.create_audio_track(
                "background_audio", 
                self._audio_source
            )
            
            # Start the playback loop
            self._running = True
            self._playback_task = asyncio.create_task(self._playback_loop())
            
            logger.info("Background audio started successfully")
            return self._track
            
        except Exception as e:
            logger.error(f"Error starting background audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.stop()
            return None
    
    async def _playback_loop(self) -> None:
        """Loop through the audio data and send frames to the audio source"""
        if not self._audio_data.size:
            logger.error("No audio data to play")
            return
        
        try:
            while self._running:
                # Play the entire audio file
                position = 0
                
                while position < len(self._audio_data) and self._running:
                    # Get the next chunk of audio
                    end_pos = min(position + self.chunk_size, len(self._audio_data))
                    chunk = self._audio_data[position:end_pos]
                    position = end_pos
                    
                    # Create an audio frame
                    from .audio_frame_utils import create_audio_frame_from_numpy
                    frame = create_audio_frame_from_numpy(
                        samples=chunk,
                        sample_rate=self.sample_rate,
                        channels=self.channels
                    )
                    
                    # Capture the frame
                    await self._audio_source.capture_frame(frame)
                    
                    # Sleep to maintain real-time playback
                    await asyncio.sleep(self.chunk_duration_ms / 1000)
                
                # If not looping, exit after one play
                if not self.loop:
                    self._running = False
                    break
                    
                logger.debug("Audio loop restarting")
                
        except asyncio.CancelledError:
            logger.info("Background audio playback cancelled")
        except Exception as e:
            logger.error(f"Error in audio playback loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def set_volume(self, volume: float) -> None:
        """
        Set the volume of the background audio.
        
        Args:
            volume: Volume level from 0.0 to 1.0
        """
        new_volume = max(0.0, min(1.0, volume))
        if abs(self.volume - new_volume) > 0.01:
            self.volume = new_volume
            logger.info(f"Background audio volume set to {self.volume}")
            
            # To apply new volume, we need to reload the audio
            # This would be applied on the next loop iteration
    
    async def stop(self) -> None:
        """Stop the background audio playback and clean up resources"""
        logger.info("Stopping background audio")
        self._running = False
        
        # Cancel playback task
        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()
            try:
                await self._playback_task
            except (asyncio.CancelledError, Exception):
                pass
        
        # Clear the audio source queue
        if self._audio_source:
            try:
                self._audio_source.clear_queue()
                await self._audio_source.aclose()
            except Exception as e:
                logger.error(f"Error closing audio source: {e}")
        
        # Clear references
        self._audio_source = None
        self._track = None
        self._playback_task = None
        
        logger.info("Background audio stopped")

def find_audio_file(file_name: str) -> Optional[str]:
    """
    Find an audio file in common project locations.
    
    Args:
        file_name: The name of the audio file to find
        
    Returns:
        str: The full path to the audio file if found, None otherwise
    """
    # Check if it's an absolute path
    if os.path.isabs(file_name) and os.path.exists(file_name):
        return file_name
        
    # Start with the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Common places to look
    locations = [
        current_dir,
        os.path.join(current_dir, "static", "data"),
        os.path.join(current_dir, "..", "static", "data"),
        os.path.join(current_dir, "..", "..", "static", "data"),
        os.path.join(current_dir, "..", "..", "..", "static", "data"),
    ]
    
    # Check each location
    for location in locations:
        full_path = os.path.join(location, file_name)
        if os.path.exists(full_path):
            logger.info(f"Found audio file at: {full_path}")
            return full_path
    
    logger.warning(f"Audio file not found: {file_name}")
    return None