from enum import Enum

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"

class TTSProvider(str, Enum):
    OPENAI = "openai" 
    GOOGLE = "google"
    UPLIFT = "uplift"
    ELEVENLABS = "elevenlabs"

class STTProvider(str, Enum):
    DEEPGRAM = "deepgram"
    OPENAI = "openai"
    GOOGLE = "google"