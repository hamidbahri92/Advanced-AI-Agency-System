import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from .utils.logging import get_logger
from .utils.persistence import PersistenceManager

logger = get_logger(__name__)

class AgentRegistry:
    """
    Registry for tracking agents created by the AI Agency.
    Provides persistence and query capabilities.
    """
    
    def __init__(self, registry_path: Path):
        """
        Initialize the agent registry.
        
        Args:
            registry_path: Path to the registry file
        """
        self.registry_path = registry_path
        self.lock = threading.RLock()  # Use RLock for nested lock acquisition
        self.persistence = PersistenceManager[Dict[str, Dict[str, Any]]](
            registry_path, 
            default_value={}, 
            auto_save=True, 
            use_cache=True
        )
        self.agents = self.persistence.load()
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new agent or update an existing one.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_info: Information about the agent
        
        Returns:
            The updated agent information
        """
        with self.lock:
            if agent_id in self.agents:
                # Update existing agent
                agent_info["updated_at"] = datetime.now().isoformat()
                self.agents[agent_id].update(agent_info)
            else:
                # Register new agent
                agent_info["created_at"] = datetime.now().isoformat()
                agent_info["updated_at"] = agent_info["created_at"]
                self.agents[agent_id] = agent_info
            
            # Save to disk
            self.persistence.save(self.agents)
            
        logger.info(f"Agent {agent_id} registered: {agent_info['name']}")
        return self.agents[agent_id]
    
    def deregister_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            True if the agent was removed, False if it didn't exist
        """
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                self.persistence.save(self.agents)
                logger.info(f"Agent {agent_id} deregistered")
                return True
            else:
                logger.warning(f"Attempted to deregister non-existent agent: {agent_id}")
                return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve information about an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Agent information or None if not found
        """
        with self.lock:
            return self.agents.get(agent_id)
    
    def list_agents(self, filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None) -> List[Dict[str, Any]]:
        """
        List all registered agents, optionally filtered.
        
        Args:
            filter_func: Optional function to filter agents
        
        Returns:
            List of agent information dictionaries
        """
        with self.lock:
            if filter_func:
                return [agent for agent in self.agents.values() if filter_func(agent)]
            return list(self.agents.values())
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Update the status of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            status: New status for the agent
        
        Returns:
            True if the agent was updated, False if it didn't exist
        """
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]["status"] = status
                self.agents[agent_id]["updated_at"] = datetime.now().isoformat()
                self.persistence.save(self.agents)
                logger.info(f"Agent {agent_id} status updated: {status}")
                return True
            else:
                logger.warning(f"Attempted to update status of non-existent agent: {agent_id}")
                return False
    
    def get_agents_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific skill.
        
        Args:
            skill: Skill to look for
        
        Returns:
            List of agent information dictionaries
        """
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if "skills" in agent and skill in agent["skills"]
            ]
    
    def get_agents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Find agents with a specific status.
        
        Args:
            status: Status to look for
        
        Returns:
            List of agent information dictionaries
        """
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if "status" in agent and agent["status"] == status
            ]
    
    def get_agents_by_model(self, model: str) -> List[Dict[str, Any]]:
        """
        Find agents using a specific model.
        
        Args:
            model: Model to look for
        
        Returns:
            List of agent information dictionaries
        """
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if "model" in agent and agent["model"] == model
            ]
    
    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for agents by name, description, or skills.
        
        Args:
            query: Search query
        
        Returns:
            List of matching agent information dictionaries
        """
        query = query.lower()
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if (
                    ("name" in agent and query in agent["name"].lower()) or
                    ("description" in agent and query in agent["description"].lower()) or
                    ("skills" in agent and any(query in skill.lower() for skill in agent["skills"]))
                )
            ]
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get all agents with 'active' status.
        
        Returns:
            List of active agent information dictionaries
        """
        return self.get_agents_by_status("active")
    
    def get_agents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Find agents that belong to a specific category.
        
        Args:
            category: Category to look for
        
        Returns:
            List of agent information dictionaries
        """
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if "category" in agent and agent["category"] == category
            ]
    
    def get_agents_by_creation_date(self, date_from: str, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find agents created within a specific date range.
        
        Args:
            date_from: Start date (inclusive) in ISO format
            date_to: End date (inclusive) in ISO format, defaults to current date
        
        Returns:
            List of agent information dictionaries
        """
        from datetime import datetime
        
        if date_to is None:
            date_to = datetime.now().isoformat()
        
        with self.lock:
            return [
                agent for agent in self.agents.values()
                if "created_at" in agent and date_from <= agent["created_at"] <= date_to
            ]
