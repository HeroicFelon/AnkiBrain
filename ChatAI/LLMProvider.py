"""
Abstract base class and implementations for different LLM providers.
Supports OpenAI, GitHub Copilot, and other providers.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any
import os


class LLMProviderType(Enum):
    """Enum for available LLM providers"""
    OPENAI = 'openai'
    GITHUB_COPILOT = 'github_copilot'


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model_name: str, temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
    
    @abstractmethod
    def get_llm(self) -> Any:
        """
        Returns the configured LLM instance for use with LangChain.
        Should return a LangChain-compatible chat model.
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if the provider has valid credentials configured"""
        pass
    
    @abstractmethod
    def get_api_key_env_var(self) -> str:
        """Return the environment variable name for the API key"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, model_name: str = 'gpt-3.5-turbo', temperature: float = 0.0):
        super().__init__(model_name, temperature)
    
    def get_llm(self) -> Any:
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(temperature=self.temperature, model_name=self.model_name)
    
    def validate_credentials(self) -> bool:
        return os.getenv('OPENAI_API_KEY') is not None
    
    def get_api_key_env_var(self) -> str:
        return 'OPENAI_API_KEY'


class GitHubCopilotProvider(LLMProvider):
    """GitHub Copilot LLM provider implementation using OpenAI-compatible API"""
    
    # Default models available through GitHub Copilot
    DEFAULT_MODEL = 'gpt-4o'
    AVAILABLE_MODELS = ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo', 'o1-preview', 'o1-mini', 'claude-3.5-sonnet']
    
    def __init__(self, model_name: str = DEFAULT_MODEL, temperature: float = 0.0):
        super().__init__(model_name, temperature)
    
    def get_llm(self) -> Any:
        from langchain.chat_models import ChatOpenAI
        
        # GitHub Copilot uses OpenAI-compatible API with custom base URL
        api_key = os.getenv(self.get_api_key_env_var())
        
        return ChatOpenAI(
            temperature=self.temperature,
            model_name=self.model_name,
            openai_api_key=api_key,
            openai_api_base="https://api.githubcopilot.com",
            # GitHub Copilot may require custom headers
            model_kwargs={
                "headers": {
                    "Editor-Version": "vscode/1.95.0",
                    "Editor-Plugin-Version": "copilot-chat/0.22.4"
                }
            }
        )
    
    def validate_credentials(self) -> bool:
        return os.getenv('GITHUB_COPILOT_TOKEN') is not None
    
    def get_api_key_env_var(self) -> str:
        return 'GITHUB_COPILOT_TOKEN'


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(
        provider_type: LLMProviderType,
        model_name: Optional[str] = None,
        temperature: float = 0.0
    ) -> LLMProvider:
        """
        Create an LLM provider instance based on the provider type.
        
        Args:
            provider_type: The type of provider to create
            model_name: Optional model name override
            temperature: Temperature setting for the LLM
            
        Returns:
            Configured LLMProvider instance
        """
        if provider_type == LLMProviderType.OPENAI:
            model = model_name or 'gpt-3.5-turbo'
            return OpenAIProvider(model_name=model, temperature=temperature)
        
        elif provider_type == LLMProviderType.GITHUB_COPILOT:
            model = model_name or GitHubCopilotProvider.DEFAULT_MODEL
            return GitHubCopilotProvider(model_name=model, temperature=temperature)
        
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def get_available_models(provider_type: LLMProviderType) -> list[str]:
        """Get list of available models for a provider type"""
        if provider_type == LLMProviderType.OPENAI:
            return [
                'gpt-4',
                'gpt-4-turbo-preview',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k'
            ]
        elif provider_type == LLMProviderType.GITHUB_COPILOT:
            return GitHubCopilotProvider.AVAILABLE_MODELS
        else:
            return []
