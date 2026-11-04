"""
LLM Provider abstraction with structured output support.
"""
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar

import instructor
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import LLMError
from apps.backend.src.core.telemetry import record_agent_metrics


T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    parsed: Optional[BaseModel] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    provider: str = ""
    raw_response: Any = None


@dataclass
class LLMMessage:
    """LLM message format."""
    role: str  # system, user, assistant
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Complete chat with optional structured output."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for token usage."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider with instructor for structured output."""
    
    MODEL_COSTS = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise LLMError("openai", "OpenAI API key not configured")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url or "https://api.openai.com/v1",
        )
        # Wrap with instructor for structured output
        self.instructor_client = instructor.from_openai(self.client, mode=instructor.Mode.JSON)
        self.default_model = settings.DEFAULT_LLM_MODEL
    
    async def complete(
        self,
        messages: List[LLMMessage],
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        model: str = None,
        **kwargs,
    ) -> LLMResponse:
        model = model or self.default_model
        
        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            if response_model:
                # Structured output with instructor
                response = await self.instructor_client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = response.model_dump_json()
                parsed = response
            else:
                # Regular completion
                completion = await self.client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = completion.choices[0].message.content
                parsed = None
            
            # Calculate usage
            input_tokens = self.count_tokens("\n".join(m.content for m in messages))
            output_tokens = self.count_tokens(content)
            cost = self.estimate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                parsed=parsed,
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost,
                model=model,
                provider="openai",
                raw_response=completion if not response_model else response,
            )
            
        except ValidationError as e:
            raise LLMError("openai", f"Validation error: {e}", model=model)
        except Exception as e:
            raise LLMError("openai", str(e), model=model)
    
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        model: str = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def count_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        costs = self.MODEL_COSTS.get(self.default_model, self.MODEL_COSTS["gpt-4-turbo-preview"])
        return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class AnthropicProvider(LLMProvider):
    """Anthropic provider with instructor for structured output."""
    
    MODEL_COSTS = {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise LLMError("anthropic", "Anthropic API key not configured")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.instructor_client = instructor.from_anthropic(self.client)
        self.default_model = "claude-3-5-sonnet-20241022"
    
    async def complete(
        self,
        messages: List[LLMMessage],
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        model: str = None,
        **kwargs,
    ) -> LLMResponse:
        model = model or self.default_model
        
        # Separate system message
        system_msg = None
        user_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            if response_model:
                response = await self.instructor_client.messages.create(
                    model=model,
                    system=system_msg,
                    messages=user_messages,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = response.model_dump_json()
                parsed = response
            else:
                completion = await self.client.messages.create(
                    model=model,
                    system=system_msg,
                    messages=user_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = completion.content[0].text
                parsed = None
            
            input_tokens = self.count_tokens(system_msg or "") + sum(
                self.count_tokens(m["content"]) for m in user_messages
            )
            output_tokens = self.count_tokens(content)
            cost = self.estimate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                parsed=parsed,
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost,
                model=model,
                provider="anthropic",
            )
            
        except ValidationError as e:
            raise LLMError("anthropic", f"Validation error: {e}", model=model)
        except Exception as e:
            raise LLMError("anthropic", str(e), model=model)
    
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        model: str = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        system_msg = None
        user_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})
        
        stream = await self.client.messages.create(
            model=model,
            system=system_msg,
            messages=user_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text
    
    def count_tokens(self, text: str) -> int:
        return len(text) // 4
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        costs = self.MODEL_COSTS.get(self.default_model, self.MODEL_COSTS["claude-3-sonnet-20240229"])
        return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, LLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_name: str = None) -> LLMProvider:
        """Get or create provider instance."""
        provider_name = provider_name or settings.DEFAULT_LLM_PROVIDER
        
        if provider_name not in cls._providers:
            if provider_name == "openai":
                cls._providers[provider_name] = OpenAIProvider()
            elif provider_name == "anthropic":
                cls._providers[provider_name] = AnthropicProvider()
            else:
                raise LLMError(provider_name, f"Unknown provider: {provider_name}")
        
        return cls._providers[provider_name]
    
    @classmethod
    async def complete(
        cls,
        messages: List[LLMMessage],
        response_model: Optional[Type[T]] = None,
        provider: str = None,
        **kwargs,
    ) -> LLMResponse:
        """Convenience method for direct completion."""
        provider_instance = cls.get_provider(provider)
        response = await provider_instance.complete(messages, response_model, **kwargs)
        
        # Record metrics
        record_agent_metrics(
            agent_role=kwargs.get("agent_role", "unknown"),
            duration=0,  # Will be updated by caller
            status="completed" if response.parsed else "failed",
            tokens=response.tokens_used,
            cost=response.cost_usd,
        )
        
        return response


# Pydantic models for structured outputs
class PlanOutput(BaseModel):
    """Planner agent output schema."""
    milestones: List[Dict[str, Any]]
    architecture_decisions: List[Dict[str, str]]
    risks: List[Dict[str, str]]


class ArchitectureOutput(BaseModel):
    """Architect agent output schema."""
    architecture: Dict[str, Any]
    api_design: Dict[str, Any]
    data_models: List[Dict[str, Any]]
    adrs: List[Dict[str, Any]]
    security_considerations: List[str]
    scalability_considerations: List[str]


class CodeFile(BaseModel):
    """Single code file output."""
    path: str
    content: str
    language: str = "python"


class BackendOutput(BaseModel):
    """Backend agent output schema."""
    files: List[CodeFile]
    database_migrations: List[Dict[str, str]]
    tests: List[CodeFile]
    dependencies: List[str]
    configuration: Dict[str, List[str]]
    deployment_notes: str


class DeploymentOutput(BaseModel):
    """DevOps agent output schema."""
    kubernetes_manifests: List[CodeFile]
    dockerfile: CodeFile
    docker_compose: CodeFile
    github_actions: CodeFile
    helm_chart: List[CodeFile]
    deployment_script: CodeFile
    rollback_script: CodeFile