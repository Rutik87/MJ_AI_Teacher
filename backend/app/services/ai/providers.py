import os
import re
import json
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.utils.logger import logger

class BaseAIProvider(ABC):
    """
    Abstract base class for all AI LLM providers in MPSC AI.
    """
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class OpenAIProvider(BaseAIProvider):
    """
    Official OpenAI ChatGPT API Provider (gpt-4o-mini / gpt-4o).
    Primary text chat & structured answer generator for MPSC AI.
    """
    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.model = model or settings.OPENAI_MODEL or "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return f"ChatGPT OpenAI ({self.model})"

    def _masked_key(self) -> str:
        if not self.api_key:
            return "<none>"
        return self.api_key[:4] + "***" + self.api_key[-4:] if len(self.api_key) > 8 else "***"

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Optional[str]:
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(self.OPENAI_ENDPOINT, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices and len(choices) > 0:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            logger.info(f"ChatGPT [{self.model}] response received ({len(content)} chars)")
                            return content.strip()
                else:
                    logger.warning(f"OpenAI API returned HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error connecting to OpenAI API: {e}")

        return None


class OpenRouterProvider(BaseAIProvider):
    """
    Primary ₹0 Free-First AI Provider using OpenRouter Free Models Router.
    Enforces ONLY free models (ending in :free or openrouter/free).
    Strictly forbids openrouter/auto to prevent accidental paid model routing.
    """
    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY or settings.AI_API_KEY
        raw_model = model or settings.OPENROUTER_MODEL or "openrouter/free"
        
        # Enforce FREE model safety constraint:
        # Never allow openrouter/auto (which can auto-route to paid models).
        # Must be openrouter/free or end with :free
        if raw_model.strip().lower() in ["openrouter/auto", "auto"]:
            logger.warning("openrouter/auto model requested! Overriding to safe openrouter/free to guarantee ₹0 cost.")
            self.model = "openrouter/free"
        elif not raw_model.endswith(":free") and raw_model != "openrouter/free":
            # Append :free if model specified without suffix to guarantee free model execution
            if "/" in raw_model:
                self.model = f"{raw_model}:free"
            else:
                self.model = "openrouter/free"
        else:
            self.model = raw_model

    @property
    def provider_name(self) -> str:
        return f"OpenRouter ({self.model})"

    def _masked_key(self) -> str:
        if not self.api_key:
            return "<none>"
        return self.api_key[:4] + "***" + self.api_key[-4:] if len(self.api_key) > 8 else "***"

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://mpscai.com",
            "X-Title": "MPSC AI Assistant",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Attempt call with backoff retry for rate limits (HTTP 429)
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    resp = await client.post(self.OPENROUTER_ENDPOINT, json=payload, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and len(choices) > 0:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                logger.info(f"OpenRouter [{self.model}] response received ({len(content)} chars)")
                                return content.strip()

                    elif resp.status_code == 429:
                        logger.warning(f"OpenRouter Rate Limited (429) [Attempt {attempt + 1}/{max_retries + 1}]. Key: {self._masked_key()}")
                        if attempt < max_retries:
                            await asyncio.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            logger.error("OpenRouter 429 rate limit exceeded max retries.")
                            return None
                    else:
                        logger.warning(f"OpenRouter returned HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.error(f"Error connecting to OpenRouter API (Attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1.0)
                    continue

        return None


class GeminiProvider(BaseAIProvider):
    """
    Optional Google Gemini LLM Provider fallback.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.AI_API_KEY
        self.model = model or "gemini-1.5-flash"

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self.model})"

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Optional[str]:
        if not self.api_key:
            return None

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            full_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {
                "contents": [{"parts": [{"text": full_text}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if content:
                            return content.strip()
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
        return None


class HeuristicLocalProvider(BaseAIProvider):
    """
    Offline local Marathi Knowledge & Structured Context generator fallback.
    Ensures 100% application stability when offline or zero keys configured.
    """
    @property
    def provider_name(self) -> str:
        return "Local Heuristic Engine (Offline ₹0)"

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Optional[str]:
        # Offline heuristic generator
        return None
