from typing import Dict, List, Any, Optional
import uuid

from google.adk.tools import BaseTool

from ..utils.logging import get_logger

logger = get_logger(__name__)

class AgentManagementTool(BaseTool):
    """Tool for managing existing agents."""
    
    def __init__(self, registry, agent_factory):
        """
        Initialize the agent management tool.
        
        Args:
            registry: Registry containing all agents
            agent_factory: Factory for managing agents
        """
        self.registry = registry
        self.agent_factory = agent_factory
        
        super().__init__(
            name="manage_agent",
            description="Manages existing agents - list, get details, update, or delete",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "update", "delete", "activate", "deactivate"],
                        "description": "The action to perform on agents"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent (required for 'get', 'update', 'delete', 'activate', and 'deactivate' actions)"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Updates to apply to the agent (for 'update' action)"
                    },
                    "filter_by_skill": {
                        "type": "string",
                        "description": "Filter agents by skill (for 'list' action)"
                    },
                    "filter_by_status": {
                        "type": "string",
                        "description": "Filter agents by status (for 'list' action)"
                    },
                    "filter_by_model": {
                        "type": "string",
                        "description": "Filter agents by model (for 'list' action)"
                    },
                    "filter_by_category": {
                        "type": "string",
                        "description": "Filter agents by category (for 'list' action)"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search for agents by name, description, or skills (for 'list' action)"
                    }
                },
                "required": ["action"]
            }
        )
    
    def run(
        self,
        action: str,
        agent_id: Optional[str] = None,
        updates: Optional[Dict[str, Any]] = None,
        filter_by_skill: Optional[str] = None,
        filter_by_status: Optional[str] = None,
        filter_by_model: Optional[str] = None,
        filter_by_category: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform the specified management action.
        
        Args:
            action: Action to perform (list, get, update, delete, activate, deactivate)
            agent_id: ID of the agent (for get, update, delete, activate, deactivate)
            updates: Updates to apply to the agent (for update)
            filter_by_skill: Filter agents by skill (for list)
            filter_by_status: Filter agents by status (for list)
            filter_by_model: Filter agents by model (for list)
            filter_by_category: Filter agents by category (for list)
            search_query: Search for agents by name, description, or skills (for list)
            
        Returns:
            Result of the action
        """
        try:
            if action == "list":
                # Apply filters based on the provided parameters
                if filter_by_skill:
                    agents = self.registry.get_agents_by_skill(filter_by_skill)
                elif filter_by_status:
                    agents = self.registry.get_agents_by_status(filter_by_status)
                elif filter_by_model:
                    agents = self.registry.get_agents_by_model(filter_by_model)
                elif filter_by_category:
                    agents = self.registry.get_agents_by_category(filter_by_category)
                elif search_query:
                    agents = self.registry.search_agents(search_query)
                else:
                    agents = self.registry.list_agents()
                
                return {
                    "status": "success",
                    "count": len(agents),
                    "agents": agents
                }
            
            elif action == "get":
                if not agent_id:
                    return {
                        "status": "error",
                        "message": "agent_id is required for 'get' action"
                    }
                
                agent_info = self.registry.get_agent(agent_id)
                if not agent_info:
                    return {
                        "status": "error",
                        "message": f"Agent with ID '{agent_id}' not found"
                    }
                
                return {
                    "status": "success",
                    "agent": agent_info
                }
            
            elif action == "update":
                if not agent_id:
                    return {
                        "status": "error",
                        "message": "agent_id is required for 'update' action"
                    }
                
                if not updates:
                    return {
                        "status": "error",
                        "message": "updates are required for 'update' action"
                    }
                
                updated_agent = self.agent_factory.update_agent(agent_id, updates)
                if not updated_agent:
                    return {
                        "status": "error",
                        "message": f"Agent with ID '{agent_id}' not found"
                    }
                
                return {
                    "status": "success",
                    "message": f"Agent '{agent_id}' updated successfully",
                    "agent": updated_agent
                }
            
            elif action == "delete":
                if not agent_id:
                    return {
                        "status": "error",
                        "message": "agent_id is required for 'delete' action"
                    }
                
                success = self.agent_factory.delete_agent(agent_id)
                
                if success:
                    return {
                        "status": "success",
                        "message": f"Agent '{agent_id}' deleted successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Agent with ID '{agent_id}' not found"
                    }
            
            elif action == "activate":
                if not agent_id:
                    return {
                        "status": "error",
                        "message": "agent_id is required for 'activate' action"
                    }
                
                success = self.agent_factory.activate_agent(agent_id)
                
                if success:
                    return {
                        "status": "success",
                        "message": f"Agent '{agent_id}' activated successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Agent with ID '{agent_id}' not found"
                    }
            
            elif action == "deactivate":
                if not agent_id:
                    return {
                        "status": "error",
                        "message": "agent_id is required for 'deactivate' action"
                    }
                
                success = self.agent_factory.deactivate_agent(agent_id)
                
                if success:
                    return {
                        "status": "success",
                        "message": f"Agent '{agent_id}' deactivated successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Agent with ID '{agent_id}' not found"
                    }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error in agent management tool: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }

class AgentStatsTool(BaseTool):
    """Tool for getting statistics about agents."""
    
    def __init__(self, registry):
        """
        Initialize the agent stats tool.
        
        Args:
            registry: Registry containing all agents
        """
        self.registry = registry
        
        super().__init__(
            name="agent_stats",
            description="Get statistics about agents in the registry",
            parameters={
                "type": "object",
                "properties": {
                    "stat_type": {
                        "type": "string",
                        "enum": ["count", "skill_distribution", "model_distribution", "status_distribution", "category_distribution"],
                        "description": "Type of statistics to retrieve"
                    },
                    "filter_by_skill": {
                        "type": "string",
                        "description": "Filter agents by skill (optional)"
                    },
                    "filter_by_status": {
                        "type": "string",
                        "description": "Filter agents by status (optional)"
                    },
                    "filter_by_model": {
                        "type": "string",
                        "description": "Filter agents by model (optional)"
                    },
                    "filter_by_category": {
                        "type": "string",
                        "description": "Filter agents by category (optional)"
                    }
                },
                "required": ["stat_type"]
            }
        )
    
    def run(
        self,
        stat_type: str,
        filter_by_skill: Optional[str] = None,
        filter_by_status: Optional[str] = None,
        filter_by_model: Optional[str] = None,
        filter_by_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about agents.
        
        Args:
            stat_type: Type of statistics to retrieve
            filter_by_skill: Filter agents by skill (optional)
            filter_by_status: Filter agents by status (optional)
            filter_by_model: Filter agents by model (optional)
            filter_by_category: Filter agents by category (optional)
            
        Returns:
            Statistics about agents
        """
        try:
            # Get agents based on filters
            agents = self._get_filtered_agents(
                filter_by_skill,
                filter_by_status,
                filter_by_model,
                filter_by_category
            )
            
            # Calculate statistics
            if stat_type == "count":
                return {
                    "status": "success",
                    "count": len(agents)
                }
            
            elif stat_type == "skill_distribution":
                skill_counts = {}
                for agent in agents:
                    for skill in agent.get("skills", []):
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
                
                return {
                    "status": "success",
                    "skill_distribution": skill_counts
                }
            
            elif stat_type == "model_distribution":
                model_counts = {}
                for agent in agents:
                    model = agent.get("model", "unknown")
                    model_counts[model] = model_counts.get(model, 0) + 1
                
                return {
                    "status": "success",
                    "model_distribution": model_counts
                }
            
            elif stat_type == "status_distribution":
                status_counts = {}
                for agent in agents:
                    status = agent.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                return {
                    "status": "success",
                    "status_distribution": status_counts
                }
            
            elif stat_type == "category_distribution":
                category_counts = {}
                for agent in agents:
                    category = agent.get("category", "unknown")
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                return {
                    "status": "success",
                    "category_distribution": category_counts
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown stat_type: {stat_type}"
                }
        except Exception as e:
            logger.error(f"Error in agent stats tool: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def _get_filtered_agents(
        self,
        filter_by_skill: Optional[str] = None,
        filter_by_status: Optional[str] = None,
        filter_by_model: Optional[str] = None,
        filter_by_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get agents based on filters.
        
        Args:
            filter_by_skill: Filter agents by skill (optional)
            filter_by_status: Filter agents by status (optional)
            filter_by_model: Filter agents by model (optional)
            filter_by_category: Filter agents by category (optional)
            
        Returns:
            List of filtered agents
        """
        # Start with all agents
        agents = self.registry.list_agents()
        
        # Apply filters
        if filter_by_skill:
            agents = [
                agent for agent in agents
                if "skills" in agent and filter_by_skill in agent["skills"]
            ]
        
        if filter_by_status:
            agents = [
                agent for agent in agents
                if "status" in agent and agent["status"] == filter_by_status
            ]
        
        if filter_by_model:
            agents = [
                agent for agent in agents
                if "model" in agent and agent["model"] == filter_by_model
            ]
        
        if filter_by_category:
            agents = [
                agent for agent in agents
                if "category" in agent and agent["category"] == filter_by_category
            ]
        
        return agents
