"""
LLM utilities for the demand/supply prototype.

We keep this small and optional:
- If API keys are not configured, agents fall back to deterministic template reasoning.

Supported providers:
- Google Gemini via google-genai (preferred when GOOGLE_API_KEY is set)
- OpenAI via autogen-ext (when OPENAI_API_KEY is set)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from dotenv import load_dotenv

from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

import google.genai as genai
from google.genai import types as genai_types


@runtime_checkable
class ReasoningClient(Protocol):
    async def generate(self, *, system: str, user: str) -> str: ...


@dataclass
class GeminiReasoningClient:
    client: genai.Client
    model: str
    temperature: float = 0.2

    async def generate(self, *, system: str, user: str) -> str:
        # google-genai is sync; run in a thread to keep our agent handlers async-friendly.
        import asyncio

        def _call() -> str:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=user,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self.temperature,
                ),
            )
            # The SDK typically exposes .text for convenience.
            text = getattr(resp, "text", None)
            if text:
                return str(text).strip()
            # Fallback: try candidates structure
            try:
                return str(resp.candidates[0].content.parts[0].text).strip()  # type: ignore[attr-defined]
            except Exception:
                return ""

        return await asyncio.to_thread(_call)


@dataclass
class OpenAIReasoningClient:
    client: OpenAIChatCompletionClient

    async def generate(self, *, system: str, user: str) -> str:
        result = await self.client.create(
            messages=[
                SystemMessage(content=system),
                UserMessage(content=user),
            ]
        )
        return (result.content or "").strip()


def build_gemini_client() -> Optional[GeminiReasoningClient]:
    """
    Create a Gemini reasoning client if GOOGLE_API_KEY is configured.

    Env vars:
    - GOOGLE_API_KEY (required)
    - GOOGLE_MODEL (optional, default: gemini-2.5-pro)
    """
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-pro")
    return GeminiReasoningClient(client=genai.Client(api_key=api_key), model=model, temperature=0.2)


def build_openai_client() -> Optional[OpenAIChatCompletionClient]:
    """
    Create an OpenAI model client if OPENAI_API_KEY is configured.

    Env vars:
    - OPENAI_API_KEY (required)
    - OPENAI_MODEL (optional, default: gpt-4o-mini)
    - OPENAI_BASE_URL (optional)
    """
    # Load .env (project root) if present
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")

    kwargs = {
        "api_key": api_key,
        "model": model,
        "temperature": 0.2,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAIChatCompletionClient(**kwargs)


def build_reasoning_client(prefer: str = "google") -> Optional[ReasoningClient]:
    """
    Returns a client that can generate reasoning text.
    Preference order:
    - if prefer == "google": Gemini first, then OpenAI
    - if prefer == "openai": OpenAI first, then Gemini
    """
    if prefer.lower() == "openai":
        oai = build_openai_client()
        if oai:
            return OpenAIReasoningClient(oai)
        gem = build_gemini_client()
        if gem:
            return gem
        return None

    gem = build_gemini_client()
    if gem:
        return gem
    oai = build_openai_client()
    if oai:
        return OpenAIReasoningClient(oai)
    return None


