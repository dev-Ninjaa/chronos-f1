"""
Granite-compatible local AI client backed by Ollama.
"""
from ai.ollamaClient import OllamaClient


class GraniteClient(OllamaClient):
    """Compatibility wrapper for existing imports."""

    def __init__(self, apiKey: str = None):
        super().__init__()
        self.checkConnection()
