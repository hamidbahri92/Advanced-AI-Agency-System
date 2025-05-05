import uuid
from pathlib import Path
import json
from typing import Dict, List, Any, Optional

from .config import Config
from .agent_registry import AgentRegistry
from .models.model_registry import model_registry
from .utils.logging import get_logger
from .communication.mcp_integration import MCPServerManager

logger = get_logger(__name__)

class AgentFactory:
    """
    Factory for creating and managing AI agents.
    """
    
    def __init__(self, registry: AgentRegistry, mcp_manager: MCPServerManager):
        """
        Initialize the agent factory.
        
        Args:
            registry: Registry for storing agent information
            mcp_manager: Manager for MCP servers
        """
        self.registry = registry
        self.mcp_manager = mcp_manager
        self.agent_cards_dir = Config.AGENT_CARDS_DIR
    
    def create_agent(
        self,
        name: str,
        description: str,
        skills: List[str],
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        mcp_servers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent with the specified parameters.
        
        Args:
            name: Name of the agent
            description: Description of the agent's purpose
            skills: List of skills the agent should have
            model: LLM model to use (optional)
            instructions: Specific instructions for the agent (optional)
            mcp_servers: List of MCP servers to connect to (optional)
            metadata: Additional metadata for the agent (optional)
            
        Returns:
            Dict containing the new agent's information
        """
        # Generate a unique ID for the agent
        agent_id = str(uuid.uuid4())
        
        # Use default model if none specified
        if not model:
            model = Config.DEFAULT_MODEL
        
        # Create agent information
        agent_info = {
            "id": agent_id,
            "name": name,
            "description": description,
            "skills": skills,
            "model": model,
            "status": "active",
            "category": metadata.get("category", "general") if metadata else "general"
        }
        
        # Add instructions if provided
        if instructions:
            agent_info["instructions"] = instructions
        
        # Add MCP servers if provided
        if mcp_servers:
            agent_info["mcp_servers"] = mcp_servers
        
        # Add additional metadata if provided
        if metadata:
            for key, value in metadata.items():
                if key not in agent_info:
                    agent_info[key] = value
        
        # Create an A2A card for the agent
        a2a_card_path = self._create_agent_card(agent_id, agent_info)
        if a2a_card_path:
            agent_info["a2a_card_path"] = str(a2a_card_path)
        
        # Register the agent
        self.registry.register_agent(agent_id, agent_info)
        
        logger.info(f"Created agent: {name} ({agent_id})")
        
        return agent_info
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: ID of the agent to delete
        
        Returns:
            True if the agent was deleted, False otherwise
        """
        # Check if the agent exists
        agent = self.registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"Attempted to delete non-existent agent: {agent_id}")
            return False
        
        # Delete the agent's A2A card if it exists
        if "a2a_card_path" in agent:
            try:
                card_path = Path(agent["a2a_card_path"])
                if card_path.exists():
                    card_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete agent card for {agent_id}: {e}")
        
        # Deregister the agent
        result = self.registry.deregister_agent(agent_id)
        
        if result:
            logger.info(f"Deleted agent: {agent['name']} ({agent_id})")
        
        return result
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing agent.
        
        Args:
            agent_id: ID of the agent to update
            updates: Dictionary of fields to update
        
        Returns:
            Updated agent information or None if the agent doesn't exist
        """
        # Check if the agent exists
        agent = self.registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"Attempted to update non-existent agent: {agent_id}")
            return None
        
        # Apply updates
        for key, value in updates.items():
            if key not in ["id", "created_at"]:  # Prevent changing immutable fields
                agent[key] = value
        
        # Update the agent's A2A card if it exists
        if "a2a_card_path" in agent:
            self._update_agent_card(agent_id, agent)
        
        # Register the updated agent
        updated_agent = self.registry.register_agent(agent_id, agent)
        
        logger.info(f"Updated agent: {agent['name']} ({agent_id})")
        
        return updated_agent
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            Agent information or None if not found
        """
        return self.registry.get_agent(agent_id)
    
    def list_agents(self, filter_func=None) -> List[Dict[str, Any]]:
        """
        List all agents, optionally filtered.
        
        Args:
            filter_func: Optional function to filter agents
        
        Returns:
            List of agent information dictionaries
        """
        return self.registry.list_agents(filter_func)
    
    def activate_agent(self, agent_id: str) -> bool:
        """
        Activate an agent.
        
        Args:
            agent_id: ID of the agent to activate
        
        Returns:
            True if the agent was activated, False otherwise
        """
        return self.registry.update_agent_status(agent_id, "active")
    
    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent.
        
        Args:
            agent_id: ID of the agent to deactivate
        
        Returns:
            True if the agent was deactivated, False otherwise
        """
        return self.registry.update_agent_status(agent_id, "inactive")
    
    def _create_agent_card(self, agent_id: str, agent_info: Dict[str, Any]) -> Optional[Path]:
        """
        Create an A2A card for an agent.
        
        Args:
            agent_id: ID of the agent
            agent_info: Agent information
        
        Returns:
            Path to the agent card or None if failed
        """
        try:
            # Ensure directory exists
            self.agent_cards_dir.mkdir(parents=True, exist_ok=True)
            
            # Create card path
            card_path = self.agent_cards_dir / f"{agent_id}.json"
            
            # Create card content
            card = {
                "agentFormat": "1.0.0",
                "info": {
                    "id": agent_id,
                    "name": agent_info.get("name", "Agent"),
                    "description": agent_info.get("description", ""),
                    "version": "1.0.0",
                    "contact": {
                        "name": agent_info.get("name", "Agent"),
                        "url": f"{Config.A2A_ENDPOINT}/agents/{agent_id}"
                    }
                },
                "servers": [
                    {
                        "url": f"{Config.A2A_ENDPOINT}/agents/{agent_id}",
                        "protocol": "a2a"
                    }
                ],
                "security": [
                    {
                        "type": "apiKey",
                        "name": "x-api-key",
                        "in": "header"
                    }
                ],
                "skills": [
                    {
                        "name": skill,
                        "description": f"Skill in {skill}"
                    }
                    for skill in agent_info.get("skills", [])
                ]
            }
            
            # Add examples if available
            if "examples" in agent_info:
                for skill_idx, skill in enumerate(card["skills"]):
                    if skill_idx < len(agent_info["examples"]):
                        skill["examples"] = agent_info["examples"][skill_idx]
            
            # Write card to file
            with open(card_path, 'w') as f:
                json.dump(card, f, indent=2)
            
            return card_path
        except Exception as e:
            logger.error(f"Failed to create agent card for {agent_id}: {e}")
            return None
    
    def _update_agent_card(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """
        Update an agent's A2A card.
        
        Args:
            agent_id: ID of the agent
            agent_info: Updated agent information
        
        Returns:
            True if the card was updated, False otherwise
        """
        try:
            card_path = Path(agent_info["a2a_card_path"])
            
            # Read existing card
            with open(card_path, 'r') as f:
                card = json.load(f)
            
            # Update card content
            card["info"]["name"] = agent_info.get("name", "Agent")
            card["info"]["description"] = agent_info.get("description", "")
            
            # Update skills
            card["skills"] = [
                {
                    "name": skill,
                    "description": f"Skill in {skill}"
                }
                for skill in agent_info.get("skills", [])
            ]
            
            # Add examples if available
            if "examples" in agent_info:
                for skill_idx, skill in enumerate(card["skills"]):
                    if skill_idx < len(agent_info["examples"]):
                        skill["examples"] = agent_info["examples"][skill_idx]
            
            # Write updated card to file
            with open(card_path, 'w') as f:
                json.dump(card, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update agent card for {agent_id}: {e}")
            return False
    
    def create_agent_instance(self, agent_id: str) -> Any:
        """
        Create an actual agent instance for the given agent ID.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            Agent instance
        
        Raises:
            ValueError: If the agent doesn't exist
        """
        # Check if the agent exists
        agent_info = self.registry.get_agent(agent_id)
        if not agent_info:
            raise ValueError(f"Agent with ID {agent_id} not found")
        
        # Get the model
        model_id = agent_info.get("model", Config.DEFAULT_MODEL)
        model = model_registry.create_model(model_id)
        
        # Create MCP toolsets if specified
        tools = []
        if "mcp_servers" in agent_info:
            for server_name in agent_info["mcp_servers"]:
                server = self.mcp_manager.get_server(server_name)
                if server:
                    tools.append(server)
        
        # In a real implementation, this would create an actual agent instance
        # For now, we'll just return the model and tools
        return {
            "agent_info": agent_info,
            "model": model,
            "tools": tools
        }
