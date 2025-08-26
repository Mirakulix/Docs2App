"""
AI provider implementations for Ollama, OpenAI, and Azure OpenAI
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Union, cast

import httpx
import ollama  # type: ignore
import openai  # type: ignore
from openai import AzureOpenAI  # type: ignore

from .config import AzureOpenAIConfig, ConfigManager, OllamaConfig, OpenAIConfig

logger = logging.getLogger(__name__)


@dataclass
class AIMessage:
    """Represents an AI message with role and content"""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class AIResponse:
    """Represents an AI response with metadata"""

    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    async def generate(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Generate a response from the AI model"""
        pass

    @abstractmethod
    async def generate_stream(
        self, messages: List[AIMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the AI model"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available"""
        pass


class OllamaProvider(AIProvider):
    """Ollama AI provider implementation"""

    def __init__(self, config: OllamaConfig):
        super().__init__(config)
        self.client = ollama.AsyncClient(host=config.base_url)

    async def generate(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Generate response using Ollama"""
        try:
            # Convert messages to Ollama format
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = await self.client.chat(
                model=self.config.model,
                messages=ollama_messages,
                options={
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                },
            )

            return AIResponse(
                content=response["message"]["content"],
                provider="ollama",
                model=self.config.model,
                finish_reason=response.get("done_reason"),
                metadata=response,
            )

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def generate_stream(
        self, messages: List[AIMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Ollama"""
        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            async for chunk in await self.client.chat(  # type: ignore
                model=self.config.model,
                messages=ollama_messages,
                stream=True,
                options={
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                },
            ):
                if chunk["message"]["content"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/api/tags", timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False


class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""

    def __init__(self, config: OpenAIConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = openai.AsyncOpenAI(api_key=config.api_key, timeout=config.timeout)

    async def generate(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Generate response using OpenAI API"""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": cast(str, msg.role), "content": cast(str, msg.content)}
                for msg in messages
            ]

            response = await self.client.chat.completions.create(  # type: ignore
                model=self.config.model,
                messages=openai_messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )

            return AIResponse(
                content=response.choices[0].message.content or "",
                provider="openai",
                model=self.config.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                metadata=(
                    response.model_dump() if hasattr(response, "model_dump") else {}
                ),
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_stream(
        self, messages: List[AIMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API"""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            stream = await self.client.chat.completions.create(  # type: ignore
                model=self.config.model,
                messages=openai_messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
            )

            async for chunk in stream:  # type: ignore
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if OpenAI API is available"""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False


class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI API provider implementation"""

    def __init__(self, config: AzureOpenAIConfig):
        super().__init__(config)
        if not all([config.api_key, config.endpoint, config.deployment_name]):
            raise ValueError(
                "Azure OpenAI requires api_key, endpoint, and deployment_name"
            )

        self.client = AzureOpenAI(
            api_key=config.api_key,
            api_version=config.api_version,
            azure_endpoint=config.endpoint or "",
            timeout=config.timeout,
        )

    async def generate(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Generate response using Azure OpenAI API"""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": cast(str, msg.role), "content": cast(str, msg.content)}
                for msg in messages
            ]

            response = self.client.chat.completions.create(
                model=self.config.deployment_name,  # Azure uses deployment name
                messages=openai_messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )

            return AIResponse(
                content=response.choices[0].message.content or "",
                provider="azure",
                model=self.config.deployment_name or "",
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                metadata=(
                    response.model_dump() if hasattr(response, "model_dump") else {}
                ),
            )

        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {e}")
            raise

    async def generate_stream(
        self, messages: List[AIMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Azure OpenAI API"""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            stream = self.client.chat.completions.create(  # type: ignore
                model=self.config.deployment_name,
                messages=openai_messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
            )

            # Azure OpenAI client may not be async in older versions
            try:
                async for chunk in stream:  # type: ignore
                    if chunk.choices[0].delta.content:  # type: ignore
                        yield chunk.choices[0].delta.content  # type: ignore
            except TypeError:
                # Fallback for sync streaming
                for chunk in stream:  # type: ignore
                    if chunk.choices[0].delta.content:  # type: ignore
                        yield chunk.choices[0].delta.content  # type: ignore

        except Exception as e:
            logger.error(f"Azure OpenAI streaming failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Azure OpenAI API is available"""
        try:
            self.client.models.list()
            return True
        except Exception:
            return False


class AIProviderManager:
    """Manages multiple AI providers and provides unified interface"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.providers: Dict[str, AIProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured AI providers"""
        config = self.config_manager.config.ai_providers

        # Initialize Ollama
        try:
            self.providers["ollama"] = OllamaProvider(config.ollama)
            logger.info("Ollama provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")

        # Initialize OpenAI
        try:
            if config.openai.api_key:
                self.providers["openai"] = OpenAIProvider(config.openai)
                logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Azure OpenAI
        try:
            if all(
                [
                    config.azure.api_key,
                    config.azure.endpoint,
                    config.azure.deployment_name,
                ]
            ):
                self.providers["azure"] = AzureOpenAIProvider(config.azure)
                logger.info("Azure OpenAI provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI provider: {e}")

    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        """Get AI provider by name or return default"""
        if provider_name is None:
            provider_name = self.config_manager.get_active_ai_provider()

        if provider_name not in self.providers:
            raise ValueError(
                f"Provider '{provider_name}' not available. Available: {list(self.providers.keys())}"
            )

        return self.providers[provider_name]

    async def generate(
        self, messages: List[AIMessage], provider: Optional[str] = None, **kwargs
    ) -> AIResponse:
        """Generate response using specified or default provider"""
        ai_provider = self.get_provider(provider)
        return await ai_provider.generate(messages, **kwargs)

    async def generate_stream(
        self, messages: List[AIMessage], provider: Optional[str] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using specified or default provider"""
        ai_provider = self.get_provider(provider)
        async for chunk in ai_provider.generate_stream(messages, **kwargs):
            yield chunk

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results

    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self.providers.keys())

    def get_provider_info(self) -> Dict[str, Dict]:
        """Get information about all providers"""
        info = {}
        for name, provider in self.providers.items():
            info[name] = {
                "config_type": type(provider.config).__name__,
                "model": getattr(provider.config, "model", "unknown"),
                "available": name in self.providers,
            }
        return info
