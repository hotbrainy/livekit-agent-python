from openai import AsyncClient
from livekit.plugins import openai
import httpx
import os

class LLM(openai.LLM):
    
    @staticmethod
    def with_custom(
        *,
        model: str = "llama3.1",
        base_url: str | None = "http://localhost:11434/v1",
        client: AsyncClient | None = None,
        temperature: float | None = None,
    ) -> openai.LLM:
        """
        Create a new instance of CUStom LLM.
        """

        # shim for not using OPENAI_API_KEY
        api_key =  os.environ.get("CUSTOM_LLM_API_KEY")
        if api_key is None:
            raise ValueError("CUSTOM_API_KEY is required")

        base_url = os.environ.get("CUSTOM_LLM_API_URL")
        if base_url is None:
            raise ValueError("CUSTOM_API_URL is required")
        

        model = os.environ.get("CUSTOM_LLM_MODEL")
        if model is None:
            raise ValueError("model is required")
        return openai.LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            client=client,
            temperature=temperature,
        )
