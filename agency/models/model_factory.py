from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class ModelFactory(ABC):
    """
    Abstract factory for creating LLM model instances.
    """
    
    @abstractmethod
    def create_model(self, model_id: str, **kwargs) -> Any:
        """
        Create a model instance for a specific model ID.
        
        Args:
            model_id: ID of the model (e.g., 'gemini-2.0-pro', 'claude-3-opus')
            **kwargs: Additional arguments for the model factory
        
        Returns:
            Model instance
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all models available through this factory.
        
        Returns:
            List of model information dictionaries
        """
        pass
    
    @abstractmethod
    def can_handle(self, model_id: str) -> bool:
        """
        Check if this factory can handle the given model ID.
        
        Args:
            model_id: ID of the model (e.g., 'gemini-2.0-pro', 'claude-3-opus')
        
        Returns:
            True if this factory can handle the model ID, False otherwise
        """
        pass


# Implementation for Gemini models
class GeminiModelFactory(ModelFactory):
    """Factory for creating Gemini model instances."""
    
    def __init__(self, api_key: Optional[str] = None, use_vertex_ai: bool = False):
        self.api_key = api_key
        self.use_vertex_ai = use_vertex_ai
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create a Gemini model instance."""
        from google.adk.models.genai_llm import Gemini
        
        # Set the API key if provided
        if self.api_key:
            kwargs["api_key"] = self.api_key
        
        # Set the use_vertex_ai flag
        kwargs["use_vertex_ai"] = self.use_vertex_ai
        
        return Gemini(model=model_id, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all Gemini models."""
        return [
            {
                "id": "gemini-2.0-pro", 
                "name": "Gemini 2.0 Pro", 
                "description": "Advanced reasoning and instruction following",
                "category": "general",
                "capabilities": ["text", "reasoning", "instruction-following"],
                "token_limit": 1000000
            },
            {
                "id": "gemini-2.0-flash", 
                "name": "Gemini 2.0 Flash", 
                "description": "Fast and efficient for routine tasks",
                "category": "fast",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 1000000
            },
            {
                "id": "gemini-2.0-vision", 
                "name": "Gemini 2.0 Vision", 
                "description": "Multimodal with image understanding",
                "category": "multimodal",
                "capabilities": ["text", "vision", "reasoning"],
                "token_limit": 1000000
            },
            {
                "id": "gemini-1.5-pro", 
                "name": "Gemini 1.5 Pro", 
                "description": "Previous generation with strong capabilities",
                "category": "general",
                "capabilities": ["text", "vision", "reasoning"],
                "token_limit": 1000000
            },
            {
                "id": "gemini-1.5-flash", 
                "name": "Gemini 1.5 Flash", 
                "description": "Previous generation optimized for speed",
                "category": "fast",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 1000000
            }
        ]
    
    def can_handle(self, model_id: str) -> bool:
        """Check if this factory can handle Gemini models."""
        return model_id.lower().startswith("gemini")


# Implementation for Claude models
class ClaudeModelFactory(ModelFactory):
    """Factory for creating Claude model instances."""
    
    def __init__(self, api_key: Optional[str] = None, use_vertex_ai: bool = False):
        self.api_key = api_key
        self.use_vertex_ai = use_vertex_ai
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create a Claude model instance."""
        from google.adk.models.lite_llm import LiteLlm
        
        # Configure the model string based on deployment
        if self.use_vertex_ai:
            from google.adk.models.anthropic_llm import Claude
            from google.adk.models.registry import LLMRegistry
            
            # Register the Claude class
            LLMRegistry.register(Claude)
            
            # Return the model ID directly for Vertex AI
            return model_id
        else:
            # Use LiteLLM for direct API access
            model_string = f"anthropic/{model_id}"
            
            return LiteLlm(model=model_string, api_key=self.api_key, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all Claude models."""
        return [
            {
                "id": "claude-3-opus-20240229", 
                "name": "Claude 3 Opus", 
                "description": "Most powerful model with exceptional understanding",
                "category": "premium",
                "capabilities": ["text", "vision", "reasoning", "coding", "instruction-following"],
                "token_limit": 200000
            },
            {
                "id": "claude-3-sonnet-20240229", 
                "name": "Claude 3 Sonnet", 
                "description": "Balance of intelligence and speed",
                "category": "general",
                "capabilities": ["text", "vision", "reasoning", "instruction-following"],
                "token_limit": 200000
            },
            {
                "id": "claude-3-haiku-20240307", 
                "name": "Claude 3 Haiku", 
                "description": "Fast and efficient for routine tasks",
                "category": "fast",
                "capabilities": ["text", "vision", "instruction-following"],
                "token_limit": 200000
            },
            {
                "id": "claude-3.5-sonnet-20240620", 
                "name": "Claude 3.5 Sonnet", 
                "description": "Latest mid-tier model with enhanced capabilities",
                "category": "general",
                "capabilities": ["text", "vision", "reasoning", "coding", "instruction-following"],
                "token_limit": 200000
            },
            {
                "id": "claude-2.1", 
                "name": "Claude 2.1", 
                "description": "Previous generation model",
                "category": "legacy",
                "capabilities": ["text", "reasoning", "instruction-following"],
                "token_limit": 100000
            }
        ]
    
    def can_handle(self, model_id: str) -> bool:
        """Check if this factory can handle Claude models."""
        return model_id.lower().startswith("claude")


# Implementation for GPT models (OpenAI)
class GPTModelFactory(ModelFactory):
    """Factory for creating GPT model instances."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create a GPT model instance."""
        from google.adk.models.lite_llm import LiteLlm
        
        # Configure the model string
        if "/" not in model_id:
            model_string = f"openai/{model_id}"
        else:
            model_string = model_id
        
        return LiteLlm(model=model_string, api_key=self.api_key, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all GPT models."""
        return [
            {
                "id": "gpt-4o", 
                "name": "GPT-4o", 
                "description": "Multimodal capabilities with optimal performance",
                "category": "premium",
                "capabilities": ["text", "vision", "reasoning", "coding", "instruction-following"],
                "token_limit": 128000
            },
            {
                "id": "gpt-4-turbo", 
                "name": "GPT-4 Turbo", 
                "description": "Advanced capabilities at higher throughput",
                "category": "premium",
                "capabilities": ["text", "reasoning", "coding", "instruction-following"],
                "token_limit": 128000
            },
            {
                "id": "gpt-3.5-turbo", 
                "name": "GPT-3.5 Turbo", 
                "description": "Fast and efficient for routine tasks",
                "category": "fast",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 16000
            },
            {
                "id": "gpt-4-vision-preview", 
                "name": "GPT-4 Vision", 
                "description": "Multimodal with image understanding",
                "category": "multimodal",
                "capabilities": ["text", "vision", "reasoning"],
                "token_limit": 128000
            }
        ]
    
    def can_handle(self, model_id: str) -> bool:
        """Check if this factory can handle GPT models."""
        return any(name in model_id.lower() for name in ["gpt", "text-davinci", "openai"])


# Implementation for Mistral models
class MistralModelFactory(ModelFactory):
    """Factory for creating Mistral model instances."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create a Mistral model instance."""
        from google.adk.models.lite_llm import LiteLlm
        
        # Configure the model string
        if "/" not in model_id:
            model_string = f"mistral/{model_id}"
        else:
            model_string = model_id
        
        return LiteLlm(model=model_string, api_key=self.api_key, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all Mistral models."""
        return [
            {
                "id": "mistral-large-latest", 
                "name": "Mistral Large", 
                "description": "Most capable Mistral model",
                "category": "premium",
                "capabilities": ["text", "reasoning", "coding", "instruction-following"],
                "token_limit": 32000
            },
            {
                "id": "mistral-medium-latest", 
                "name": "Mistral Medium", 
                "description": "Balanced performance and efficiency",
                "category": "general",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 32000
            },
            {
                "id": "mistral-small-latest", 
                "name": "Mistral Small", 
                "description": "Fast and cost-effective",
                "category": "fast",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 32000
            },
            {
                "id": "open-mistral-7b", 
                "name": "Open Mistral 7B", 
                "description": "Open-source 7B parameter model",
                "category": "open-source",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 8000
            }
        ]
    
    def can_handle(self, model_id: str) -> bool:
        """Check if this factory can handle Mistral models."""
        return "mistral" in model_id.lower()


# Implementation for Llama models (Meta)
class LlamaModelFactory(ModelFactory):
    """Factory for creating Llama model instances."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create a Llama model instance."""
        from google.adk.models.lite_llm import LiteLlm
        
        # Configure the model string
        if "/" not in model_id:
            model_string = f"meta/{model_id}"
        else:
            model_string = model_id
        
        return LiteLlm(model=model_string, api_key=self.api_key, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all Llama models."""
        return [
            {
                "id": "llama-3-70b-instruct", 
                "name": "Llama 3 70B Instruct", 
                "description": "Largest Llama 3 model with exceptional capabilities",
                "category": "premium",
                "capabilities": ["text", "reasoning", "coding", "instruction-following"],
                "token_limit": 8000
            },
            {
                "id": "llama-3-8b-instruct", 
                "name": "Llama 3 8B Instruct", 
                "description": "Efficient Llama 3 model for routine tasks",
                "category": "fast",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 8000
            },
            {
                "id": "llama-2-70b-chat", 
                "name": "Llama 2 70B Chat", 
                "description": "Previous generation Llama model",
                "category": "legacy",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 4000
            },
            {
                "id": "llama-2-13b-chat", 
                "name": "Llama 2 13B Chat", 
                "description": "Efficient previous generation Llama model",
                "category": "legacy",
                "capabilities": ["text", "instruction-following"],
                "token_limit": 4000
            }
        ]
    
    def can_handle(self, model_id: str) -> bool:
        """Check if this factory can handle Llama models."""
        return "llama" in model_id.lower()
