from openai import AsyncClient
from livekit.plugins import openai
import httpx
import os
from .models import (
    GroqChatModels,
    TogetherChatModels,
)
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

    @staticmethod
    def with_groq(
        *,
        model: str | GroqChatModels = "llama3-8b-8192",
        api_key: str | None = None,
        base_url: str | None = "https://api.groq.com/openai/v1",
        client: AsyncClient | None = None,
        user: str | None = None,
        temperature: float | None = None,
    ) -> openai.LLM:
        """
        Create a new instance of Groq LLM.

        ``api_key`` must be set to your Groq API key, either using the argument or by setting
        the ``GROQ_API_KEY`` environmental variable.
        """

        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if api_key is None:
            raise ValueError(
                "Groq API key is required, either as argument or set GROQ_API_KEY environmental variable"
            )

        return LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            client=client,
            user=user,
            temperature=temperature,
        )
