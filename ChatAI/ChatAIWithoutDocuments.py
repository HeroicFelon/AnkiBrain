import json
from os import path
from typing import Tuple

from langchain import ConversationChain
from langchain.memory import ConversationBufferMemory

from ChatInterface import ChatInterface
from LLMProvider import LLMProviderFactory, LLMProviderType

user_data_dir = path.join(
    path.abspath(path.dirname(__file__)),
    '..',
    'user_files'
)

settings_path = path.join(user_data_dir, 'settings.json')


class ChatAIWithoutDocuments(ChatInterface):
    def __init__(self, verbose=False):
        temperature = 0
        model_name = 'gpt-3.5-turbo'
        provider_type = LLMProviderType.OPENAI  # default
        
        with open(settings_path, 'r') as f:
            data = json.load(f)
            temperature = data.get('temperature', 0)
            model_name = data.get('llmModel', 'gpt-3.5-turbo')
            
            # Get provider type from settings
            provider_str = data.get('llmProvider', 'openai')
            try:
                provider_type = LLMProviderType(provider_str)
            except ValueError:
                provider_type = LLMProviderType.OPENAI

        # Create LLM using provider factory
        provider = LLMProviderFactory.create_provider(
            provider_type=provider_type,
            model_name=model_name,
            temperature=temperature
        )
        self.llm = provider.get_llm()
        
        self.memory = ConversationBufferMemory()
        self.conversationChain = ConversationChain(llm=self.llm, memory=self.memory, verbose=verbose)

    def human_message(self, query: str) -> Tuple[str, None]:
        return self.conversationChain.predict(input=query), None

    def clear_memory(self):
        self.memory.clear()
