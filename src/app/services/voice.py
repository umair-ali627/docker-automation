import json
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("voice-service")

class VoiceService:
    """Service for retrieving and filtering voice providers and voices."""
    
    def __init__(self, voices_file_path: str = None):
        """
        Initialize the voice service.
        
        Args:
            voices_file_path: Optional path to the voices JSON file.
                If not provided, uses the default path relative to this file.
        """
        if voices_file_path is None:
            # Default path is in the static directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.voices_file_path = os.path.join(current_dir, '..', '..', '..', 'static', 'data', 'voices.json')
        else:
            self.voices_file_path = voices_file_path
            
        self._voices_cache = None
    
    def _load_voices(self) -> List[Dict[str, Any]]:
        """Load voices from the JSON file."""
        if self._voices_cache is not None:
            return self._voices_cache
            
        try:
            with open(self.voices_file_path, 'r') as f:
                voices = json.load(f)
                self._voices_cache = voices
                return voices
        except Exception as e:
            logger.error(f"Error loading voices from {self.voices_file_path}: {e}")
            return []
    
    def get_all_voices(self) -> List[Dict[str, Any]]:
        """Get all available voices."""
        return self._load_voices()
    
    def get_voices_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """
        Get voices filtered by provider.
        
        Args:
            provider: The voice provider (e.g., 'openai', 'cartesia')
            
        Returns:
            List of voice dictionaries for the specified provider
        """
        voices = self._load_voices()
        return [voice for voice in voices if voice.get('provider') == provider]
    
    def get_voice_by_id(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific voice by its ID.
        
        Args:
            voice_id: The unique ID of the voice
            
        Returns:
            Voice dictionary or None if not found
        """
        voices = self._load_voices()
        for voice in voices:
            if voice.get('id') == voice_id:
                return voice
        return None
    
    def get_voice_by_provider_id(self, provider: str, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific voice by provider and provider ID.
        
        Args:
            provider: The voice provider (e.g., 'openai')
            provider_id: The provider-specific ID (e.g., 'alloy')
            
        Returns:
            Voice dictionary or None if not found
        """
        voices = self._load_voices()
        for voice in voices:
            if voice.get('provider') == provider and voice.get('providerId') == provider_id:
                return voice
        return None
    
    def get_providers(self) -> List[str]:
        """
        Get a list of all available providers.
        
        Returns:
            List of provider names
        """
        voices = self._load_voices()
        providers = set(voice.get('provider') for voice in voices if voice.get('provider'))
        return list(providers)

# Create a singleton instance
voice_service = VoiceService()