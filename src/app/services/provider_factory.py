from typing import Dict, Any
from livekit.agents import llm
from livekit.plugins import deepgram, openai, elevenlabs, uplift, google
from livekit.plugins.elevenlabs.tts import Voice, VoiceSettings

from ..schemas.provider_types import LLMProvider, TTSProvider, STTProvider
from ..core.config import settings

import logging

logger = logging.getLogger("provider-factory")

class ProviderFactory:
    @staticmethod
    def create_llm(provider: str, options: Dict[str, Any]) -> llm.LLM:
        """Create LLM based on provider type and options"""
        if provider == LLMProvider.OPENAI.value:
            return openai.LLM(
                api_key=settings.OPENAI_API_KEY,
                model=options.get('model', 'gpt-4o'),
                temperature=options.get('temperature', 0.7),
                max_tokens=options.get('max_tokens', None)
            )
        # elif provider == LLMProvider.GOOGLE.value:
        #     return google.LLM(
        #         api_key=settings.GOOGLE_API_KEY,
        #         model=options.get('model', 'gemini-pro'),
        #         temperature=options.get('temperature', 0.7)
        #     )
            # return google.LLM(
            #     api_key=settings.GOOGLE_API_KEY,
            #     model=options.get('model', 'gemini-pro'),
            #     temperature=options.get('temperature', 0.7)
            # )
        else:
            # Fallback to OpenAI
            return openai.LLM(
                api_key=settings.OPENAI_API_KEY,
                model='gpt-4o',
                temperature=0.7
            )
    # add model 
    @staticmethod
    def create_tts(provider: str, options: Dict[str, Any]) -> Any:
        """Create TTS based on provider type and options"""
        if provider == TTSProvider.OPENAI.value:
            return openai.TTS(
                api_key=settings.OPENAI_API_KEY,
                model=options.get('model', 'tts-1'),
                voice=options.get('voice', 'alloy'),
                speed=options.get('speed', 1.0)
            )
        elif provider == TTSProvider.GOOGLE.value:
            # Implementation needed for Google
            return google.TTS(
                api_key=settings.GOOGLE_API_KEY,
                voice=options.get('voice', 'en-US-Neural2-F'),
                speaking_rate=options.get('speaking_rate', 1.0),
                pitch=options.get('pitch', 0.0)
            )
        elif provider == TTSProvider.ELEVENLABS.value:
            # Create the Voice object
            id=options.get('voice', '2BJW5coyhAzSr8STdHbE')
            name=options.get('voice_name', "Edward")

            voice_settings = VoiceSettings(
                    stability=options.get('stability', 0.71), # [0.0 - 1.0]
                    similarity_boost=options.get('similarity_boost', 0.5), # [0.0 - 1.0]
                    style=options.get('style', 0.0), # [0.0 - 1.0]
                    speed=options.get('speed', 1.0),  # [0.8 - 1.2]
                    use_speaker_boost=options.get('use_speaker_boost', True)
                )

            voice = Voice(
                id=id,
                name=name,
                category="premade",
                settings=voice_settings,
            )
            return elevenlabs.TTS(
                api_key=settings.ELEVENLABS_API_KEY,
                model=options.get('model', 'eleven_flash_v2_5'),
                voice=voice
            )
        elif provider == TTSProvider.UPLIFT.value:
            return uplift.TTS(
                api_key=settings.UPLIFT_API_KEY,
                voice=options.get('voice', 'v_kwmp7zxt') # AvailableVoices = [ "v_kwmp7zxt", "v_yypgzenx", "v_30s70t3a" ]
            )
        else:
            # Fallback to OpenAI
            return openai.TTS(
                api_key=settings.OPENAI_API_KEY,
                model=options.get('model', 'tts-1'),
                voice=options.get('voice', 'alloy'),
                speed=options.get('speed', 1.0)
            )
    
    @staticmethod
    def create_stt(provider: str, options: Dict[str, Any], is_telephony: bool = False) -> Any:
        """Create STT based on provider type and options"""
        if provider == STTProvider.DEEPGRAM.value:
            model = options.get('model', 'nova-3-general')
            if is_telephony:
                model = options.get('model_telephony', 'nova-2-phonecall')
                
            return deepgram.STT(
                api_key=settings.DEEPGRAM_API_KEY,
                model=model,
                language=options.get('language', 'en'),
            )
        
        elif provider == STTProvider.OPENAI.value:
            return openai.STT(
                api_key=settings.OPENAI_API_KEY,
                model=options.get('model', 'whisper-1'),
                language=options.get('language', 'en')
            )

        elif provider == STTProvider.GOOGLE.value:
            # Implementation needed for Google
            raise NotImplementedError("Google STT support not yet implemented")
            # return google.STT(
            #     api_key=settings.GOOGLE_API_KEY,
            #     model=options.get('model', 'latest'),
            #     language_code=options.get('language_code', 'en-US')
            # )
        else:
            # Fallback to Deepgram
            return deepgram.STT(
                api_key=settings.DEEPGRAM_API_KEY,
                model='nova-3-general'
            )