from enum import Enum

class LLMModel(str, Enum):
    """Available OpenAI LLM models for agents."""
    # OpenAI models
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4_VISION = "gpt-4-vision-preview"
    
    # Google models
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    
    def __str__(self) -> str:
        return self.value