# backend/agents/llm_client.py

import os
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path=env_path)


class LLMClient(ABC):
    """Interface for the LLM client."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 400,
        temperature: float = 0.3
    ) -> str:
        ...


class APILlmClient(LLMClient):
    """
    Calls an OpenAI-compatible chat completions API.
    Works with Groq, OpenAI, Azure OpenAI, and other compatible providers.
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        model_name: str = None
    ):
        self.base_url = base_url or os.getenv("API_LLM_BASE_URL")
        self.api_key = api_key or os.getenv("API_LLM_KEY")
        self.model_name = model_name or os.getenv("API_LLM_MODEL_NAME")

        if not self.base_url:
            raise ValueError("API_LLM_BASE_URL must be set")

        if not self.api_key:
            raise ValueError("API_LLM_KEY must be set")

        if not self.model_name:
            raise ValueError("API_LLM_MODEL_NAME must be set")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 400,
        temperature: float = 0.3
    ) -> str:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        return result["choices"][0]["message"]["content"].strip()


# Cached API client instance
_client_instance = None


def get_llm_client() -> LLMClient:
    global _client_instance

    if _client_instance is None:
        _client_instance = APILlmClient()

    return _client_instance