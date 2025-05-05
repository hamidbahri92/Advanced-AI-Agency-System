import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, TypeVar, Generic

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

class PersistenceManager(Generic[T]):
    """
    Generic persistence manager for storing and retrieving data.
    
    This class provides methods for saving and loading data to/from JSON and pickle files.
    It also supports caching and automatic saving.
    """
    
    def __init__(self, file_path: Path, default_value: T = None, auto_save: bool = True, use_cache: bool = True):
        """
        Initialize the persistence manager.
        
        Args:
            file_path: Path to the file
            default_value: Default value to return if file doesn't exist
            auto_save: Whether to automatically save data when updated
            use_cache: Whether to cache data in memory
        """
        self.file_path = file_path
        self.default_value = default_value
        self.auto_save = auto_save
        self.use_cache = use_cache
        self._cache = None
    
    def save(self, data: T) -> bool:
        """
        Save data to the file.
        
        Args:
            data: Data to save
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create parent directory if it doesn't exist
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine file format
            if self.file_path.suffix.lower() == ".json":
                return self._save_json(data)
            elif self.file_path.suffix.lower() in [".pkl", ".pickle"]:
                return self._save_pickle(data)
            else:
                # Default to JSON
                return self._save_json(data)
        except Exception as e:
            logger.error(f"Failed to save data to {self.file_path}: {e}")
            return False
    
    def load(self) -> T:
        """
        Load data from the file.
        
        Returns:
            Loaded data or default value if failed
        """
        # Return cached value if available
        if self.use_cache and self._cache is not None:
            return self._cache
        
        try:
            # Check if file exists
            if not self.file_path.exists():
                return self.default_value
            
            # Determine file format
            if self.file_path.suffix.lower() == ".json":
                data = self._load_json()
            elif self.file_path.suffix.lower() in [".pkl", ".pickle"]:
                data = self._load_pickle()
            else:
                # Default to JSON
                data = self._load_json()
            
            # Cache the data
            if self.use_cache:
                self._cache = data
            
            return data
        except Exception as e:
            logger.error(f"Failed to load data from {self.file_path}: {e}")
            return self.default_value
    
    def update(self, updater_func) -> bool:
        """
        Update data using an updater function.
        
        Args:
            updater_func: Function that takes the current data and returns the updated data
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Load current data
            current_data = self.load()
            
            # Update data
            updated_data = updater_func(current_data)
            
            # Cache the updated data
            if self.use_cache:
                self._cache = updated_data
            
            # Save data if auto_save is enabled
            if self.auto_save:
                return self.save(updated_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update data: {e}")
            return False
    
    def clear_cache(self):
        """Clear the cached data."""
        self._cache = None
    
    def _save_json(self, data: T) -> bool:
        """Save data as JSON."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to {self.file_path}: {e}")
            return False
    
    def _load_json(self) -> T:
        """Load data from JSON."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {self.file_path}: {e}")
            raise
    
    def _save_pickle(self, data: T) -> bool:
        """Save data as pickle."""
        try:
            with open(self.file_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save pickle to {self.file_path}: {e}")
            return False
    
    def _load_pickle(self) -> T:
        """Load data from pickle."""
        try:
            with open(self.file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load pickle from {self.file_path}: {e}")
            raise
            
class JSONPersistence:
    """Simplified persistence class for JSON data."""
    
    @staticmethod
    def save(file_path: Path, data: Any) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            file_path: Path to the file
            data: Data to save
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to {file_path}: {e}")
            return False
    
    @staticmethod
    def load(file_path: Path, default_value: Any = None) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the file
            default_value: Default value to return if file doesn't exist
        
        Returns:
            Loaded data or default value if failed
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return default_value
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {e}")
            return default_value
