# backend/agents/llm_client.py
import os
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path=env_path)


class LLMClient(ABC):
    """Every backend (local or API) must implement this single method."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
        ...


class LocalLlamaClient(LLMClient):
    """Runs a local GGUF model via llama-cpp-python. No internet needed."""

    def __init__(self, model_path: str = None):
        from llama_cpp import Llama
        resolved_path = model_path or os.path.join(
            os.path.dirname(__file__), "..", os.getenv("LOCAL_MODEL_PATH", "../models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        )
        self.llm = Llama(
            model_path=resolved_path,
            n_ctx=4096,
            n_threads=4,
            verbose=False
        )

    # def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
    #     output = self.llm(
    #         prompt,
    #         max_tokens=max_tokens,
    #         temperature=temperature,
    #         stop=["</s>", "[INST]"]
    #     )
    #     return output["choices"][0]["text"].strip()

    # Update LocalLlamaClient.generate() in backend/agents/llm_client.py
    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        output = self.llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "[INST]"]
        )
        return output["choices"][0]["text"].strip()


class APILlmClient(LLMClient):
    """
    Calls any OpenAI-compatible chat completions endpoint.
    Works for Nomura's API, OpenAI, Azure OpenAI, most hosted LLM providers
    that follow the standard /chat/completions shape.
    """

    def __init__(self, base_url: str = None, api_key: str = None, model_name: str = None):
        self.base_url = base_url or os.getenv("API_LLM_BASE_URL")
        self.api_key = api_key or os.getenv("API_LLM_KEY")
        self.model_name = model_name or os.getenv("API_LLM_MODEL_NAME")

        if not self.base_url or not self.api_key:
            raise ValueError(
                "API_LLM_BASE_URL and API_LLM_KEY must be set in .env when LLM_PROVIDER=api"
            )

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()


# ── Factory function — the only thing the rest of the app calls ──
_client_instance = None

def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    provider = os.getenv("LLM_PROVIDER", "local").lower()

    if provider == "local":
        _client_instance = LocalLlamaClient()
    elif provider == "api":
        _client_instance = APILlmClient()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Use 'local' or 'api'.")

    return _client_instance