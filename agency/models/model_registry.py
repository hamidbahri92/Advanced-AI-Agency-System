from typing import Dict, Any, Optional, Type, List
import importlib
from pathlib import Path

from .model_factory import ModelFactory
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ModelRegistry:
    """
    Registry for LLM models that can be used in the agency.
    """
    
    def __init__(self):
        self._factories: Dict[str, ModelFactory] = {}
        self._model_classes: Dict[str, Type] = {}
        self._default_factory = None
    
    def register_factory(self, model_type: str, factory: ModelFactory, is_default: bool = False):
        """
        Register a model factory for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'gemini', 'claude', 'gpt')
            factory: Model factory instance
            is_default: Whether this factory should be the default
        """
        self._factories[model_type.lower()] = factory
        
        if is_default or self._default_factory is None:
            self._default_factory = factory
    
    def register_model_class(self, model_type: str, model_class: Type):
        """
        Register a model class for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'gemini', 'claude', 'gpt')
            model_class: Model class
        """
        self._model_classes[model_type.lower()] = model_class
    
    def get_factory(self, model_type: Optional[str] = None) -> Optional[ModelFactory]:
        """
        Get a model factory for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'gemini', 'claude', 'gpt')
        
        Returns:
            Model factory instance or default factory if model_type is None
        """
        if model_type is None:
            return self._default_factory
        
        return self._factories.get(model_type.lower())
    
    def get_model_class(self, model_type: str) -> Optional[Type]:
        """
        Get a model class for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'gemini', 'claude', 'gpt')
        
        Returns:
            Model class
        """
        return self._model_classes.get(model_type.lower())
    
    def create_model(self, model_id: str, **kwargs) -> Any:
        """
        Create a model instance for a specific model ID.
        
        Args:
            model_id: ID of the model (e.g., 'gemini-2.0-pro', 'claude-3-opus')
            **kwargs: Additional arguments for the model factory
        
        Returns:
            Model instance
        
        Raises:
            ValueError: If no factory can handle the model ID
        """
        # Try to determine the model type from the ID
        model_type = self._determine_model_type(model_id)
        
        if model_type and model_type.lower() in self._factories:
            # Use the determined factory
            factory = self._factories[model_type.lower()]
        elif self._default_factory:
            # Use the default factory
            factory = self._default_factory
        else:
            # No factory available
            raise ValueError(f"No factory available for model ID: {model_id}")
        
        # Create the model
        return factory.create_model(model_id, **kwargs)
    
    def _determine_model_type(self, model_id: str) -> Optional[str]:
        """
        Determine the model type from the model ID.
        
        Args:
            model_id: ID of the model (e.g., 'gemini-2.0-pro', 'claude-3-opus')
        
        Returns:
            Model type or None if unknown
        """
        model_id = model_id.lower()
        
        if model_id.startswith("gemini"):
            return "gemini"
        elif model_id.startswith("claude"):
            return "claude"
        elif any(name in model_id for name in ["gpt", "text-davinci", "openai"]):
            return "gpt"
        elif "mistral" in model_id:
            return "mistral"
        elif "llama" in model_id:
            return "llama"
        elif "vertex" in model_id:
            return "vertex"
        elif "palm" in model_id:
            return "palm"
        elif "bard" in model_id:
            return "bard"
        
        return None
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models that can be used.
        
        Returns:
            List of model information dictionaries
        """
        all_models = []
        
        for model_type, factory in self._factories.items():
            try:
                models = factory.list_models()
                for model in models:
                    model["type"] = model_type
                all_models.extend(models)
            except Exception as e:
                logger.error(f"Failed to list models for {model_type}: {e}")
        
        return all_models
    
    def import_model_modules(self, base_module: str = "ai_agency.models"):
        """
        Import all model modules to register model factories and classes.
        
        Args:
            base_module: Base module path
        """
        try:
            module = importlib.import_module(base_module)
            module_path = Path(module.__file__).parent
            
            for file_path in module_path.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue
                
                module_name = file_path.stem
                try:
                    importlib.import_module(f"{base_module}.{module_name}")
                except Exception as e:
                    logger.error(f"Failed to import module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to import model modules: {e}")
    
    def get_model_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group available models by category.
        
        Returns:
            Dictionary of model categories with lists of models
        """
        categories = {}
        
        for model in self.list_available_models():
            category = model.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(model)
        
        return categories
    
    def get_recommended_model(self, task_type: str) -> Optional[str]:
        """
        Get a recommended model for a specific task type.
        
        Args:
            task_type: Type of task (e.g., 'text-generation', 'chat', 'coding')
        
        Returns:
            Model ID or None if no recommendation available
        """
        # Define task-model mapping
        task_models = {
            "chat": "gemini-2.0-pro",
            "text-generation": "claude-3-opus-20240229",
            "coding": "claude-3-opus-20240229",
            "summarization": "claude-3-sonnet-20240229",
            "reasoning": "claude-3-opus-20240229",
            "translation": "gemini-2.0-pro",
            "qa": "claude-3-sonnet-20240229",
            "vision": "gemini-2.0-vision",
            "fast-response": "claude-3-haiku-20240307",
        }
        
        return task_models.get(task_type)


# Singleton instance
model_registry = ModelRegistry()
