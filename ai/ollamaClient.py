"""
Ollama client helpers for local AI generation.
"""
import os
import re
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class OllamaClient:
    def __init__(self, modelName: str = None, baseUrl: str = None):
        self.modelName = modelName or os.getenv("OLLAMA_MODEL", "granite3.3:2b")
        self.baseUrl = (baseUrl or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.availableModels = [self.modelName]

    def _generate_url(self) -> str:
        return f"{self.baseUrl}/api/generate"

    def _chat_url(self) -> str:
        return f"{self.baseUrl}/api/chat"

    def checkConnection(self) -> bool:
        try:
            response = requests.get(f"{self.baseUrl}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                names = [model.get("name") for model in models if model.get("name")]
                if names:
                    self.availableModels = names
                if self.modelName not in self.availableModels:
                    print(f"Warning: Ollama model {self.modelName} was not listed by /api/tags")
                print("Connected to Ollama")
                print(f"   Model: {self.modelName}")
                return True
            print(f"Ollama API error: {response.status_code}")
            return False
        except Exception as e:
            print(f"Could not connect to Ollama: {e}")
            return False

    def isAvailable(self) -> bool:
        return self.checkConnection()

    def listModels(self) -> List[str]:
        return self.availableModels

    def generate(
        self,
        prompt: str,
        modelName: str = None,
        temperature: float = 0.7,
        maxTokens: int = 150,
        system: str = None,
    ) -> Optional[str]:
        try:
            payload = {
                "model": modelName or self.modelName,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": maxTokens,
                    "top_p": 0.9,
                },
            }
            if system:
                payload["system"] = system

            response = requests.post(self._generate_url(), json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "").strip() or None

            print(f"Ollama generation error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return None

    def chat(self, messages: List[Dict], modelName: str = None, maxTokens: int = 150) -> Optional[str]:
        try:
            payload = {
                "model": modelName or self.modelName,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": maxTokens,
                    "top_p": 0.9,
                },
            }
            response = requests.post(self._chat_url(), json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "").strip() or None

            print(f"Ollama chat error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        except Exception as e:
            print(f"Ollama chat error: {e}")
            return None


def clean_commentary(text: Optional[str], max_lines: int = 3) -> Optional[str]:
    """Normalize model output and aggressively reject fragments / garbage."""
    if not text:
        return None

    text = text.strip().strip('"').strip("'").strip()
    if not text:
        return None

    # Strip markdown code fences
    text = re.sub(r"^```(?:text|json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    # Strip common prefixes the model adds
    text = re.sub(
        r"^(commentary|answer|output|response|result|here is|here's)\s*[:=]\s*",
        "", text, flags=re.IGNORECASE,
    ).strip()

    # Strip speaker labels like "Fan:" or "Engineer:"
    text = re.sub(r"^(fan|engineer|commentator)\s*:\s*", "", text, flags=re.IGNORECASE).strip()

    text = text.replace("\\n", "\n")

    # Remove wrapping quotes that survived first pass
    if len(text) > 2 and text[0] in ('"', "'") and text[-1] == text[0]:
        text = text[1:-1].strip()

    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        # Strip bullet / numbered-list prefixes
        line = re.sub(r"^\s*[-*•]\s*", "", line)
        line = re.sub(r"^\s*\d+[.)]\s*", "", line)
        # Strip markdown headers
        line = re.sub(r"^#+\s*", "", line)
        line = line.strip()
        if not line:
            continue
        # Reject lines that are just a driver code (e.g. "VER", "HAM", "LEC")
        if re.fullmatch(r"[A-Z]{2,4}", line):
            continue
        # Reject lines that look like JSON
        if line.startswith("{") or line.startswith("["):
            continue
        lines.append(line)

    if not lines:
        return None

    cleaned = "\n".join(lines[:max_lines]).strip()

    # Count real English words (3+ letters)
    real_words = re.findall(r"[A-Za-z]{3,}", cleaned)
    if len(real_words) < 6:
        return None

    # Reject known garbage tokens regardless of surrounding text
    upper = cleaned.upper().replace(" ", "")
    _GARBAGE = {"VERS", "VER", "HAM", "LEC", "NOR", "PIA", "SAI", "RUS", "PER",
                "NULL", "NONE", "N/A", "NA", "UNKNOWN", "ERROR", "UNDEFINED"}
    if upper in _GARBAGE:
        return None

    return cleaned
