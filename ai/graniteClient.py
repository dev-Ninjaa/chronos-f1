"""
Google Gemini AI Client
Handles communication with Google Gemini API
"""
import os
import requests
import json
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GraniteClient:
    """Renamed to maintain compatibility, but now uses Gemini"""
    
    def __init__(self, apiKey: str = None):
        self.apiKey = apiKey or os.getenv('GEMINI_API_KEY')
        if not self.apiKey:
            print("⚠️ GEMINI_API_KEY not found in environment variables")
            self.apiKey = None
        self.modelName = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.baseUrl = "https://generativelanguage.googleapis.com/v1beta"
        self.availableModels = [self.modelName]
        self._checkConnection()
    
    def _checkConnection(self):
        try:
            # Test API key with a simple request
            url = f"{self.baseUrl}/models/{self.modelName}?key={self.apiKey}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Connected to Google Gemini API")
                print(f"   Model: {self.modelName}")
                return True
            else:
                print(f"⚠️ Gemini API error: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Could not connect to Gemini API: {e}")
            return False
    
    def isAvailable(self) -> bool:
        return True  # API-based, always available if key is valid
    
    def listModels(self) -> List[str]:
        return self.availableModels
    
    def generate(self, prompt: str, modelName: str = None, 
                 temperature: float = 0.7, maxTokens: int = 150) -> Optional[str]:
        try:
            url = f"{self.baseUrl}/models/{self.modelName}:generateContent?key={self.apiKey}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": maxTokens,
                    "topP": 0.9
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return text.strip()
                else:
                    print(f"No candidates in response")
                    return None
            else:
                print(f"Gemini API error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Generation error: {e}")
            return None
    
    def chat(self, messages: List[Dict], modelName: str = None) -> Optional[str]:
        """
        Chat with Gemini using message history
        messages format: [{"role": "user", "content": "text"}]
        """
        try:
            url = f"{self.baseUrl}/models/{self.modelName}:generateContent?key={self.apiKey}"
            
            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 150
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return text.strip()
            
            return None
                
        except Exception as e:
            print(f"Chat error: {e}")
            return None
