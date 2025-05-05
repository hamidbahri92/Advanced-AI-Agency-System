from typing import Dict, List, Any, Optional
import uuid

from google.adk.tools import BaseTool

from ..utils.logging import get_logger

logger = get_logger(__name__)

class AgentCreationTool(BaseTool):
    """Tool for creating new agents."""
    
    def __init__(self, agent_factory):
        """
        Initialize the agent creation tool.
        
        Args:
            agent_factory: Factory for creating agents
        """
        self.agent_factory = agent_factory
        
        super().__init__(
            name="create_agent",
            description="Creates a new specialized agent with custom capabilities",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the agent to create"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the agent's purpose and capabilities"
                    },
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of skills or domains the agent should be specialized in"
                    },
                    "model": {
                        "type": "string",
                        "description": "The LLM model to use for this agent (optional)"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Specific instructions for the agent (optional)"
                    },
                    "mcp_servers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of MCP servers to connect to (optional)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the agent (optional)"
                    },
                    "examples": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "description": "Example queries for each skill (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the agent (e.g., 'productivity', 'creative', 'analysis') (optional)"
                    }
                },
                "required": ["name", "description", "skills"]
            }
        )
    
    def run(
        self,
        name: str,
        description: str,
        skills: List[str],
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        mcp_servers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        examples: Optional[List[List[str]]] = None,
        category: Optional[str] = None
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
            examples: Example queries for each skill (optional)
            category: Category of the agent (optional)
            
        Returns:
            Dict containing the new agent's information
        """
        try:
            # Prepare metadata
            full_metadata = metadata or {}
            if category:
                full_metadata["category"] = category
            if examples:
                full_metadata["examples"] = examples
            
            # Create the agent
            agent_info = self.agent_factory.create_agent(
                name=name,
                description=description,
                skills=skills,
                model=model,
                instructions=instructions,
                mcp_servers=mcp_servers,
                metadata=full_metadata
            )
            
            return {
                "status": "success",
                "message": f"Agent '{name}' created successfully",
                "agent_id": agent_info["id"],
                "agent_details": agent_info
            }
        except Exception as e:
            logger.error(f"Failed to create agent '{name}': {e}")
            return {
                "status": "error",
                "message": f"Failed to create agent: {str(e)}"
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models for creating agents.
        
        Returns:
            List of model information dictionaries
        """
        try:
            from ..models.model_registry import model_registry
            return model_registry.list_available_models()
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def get_available_mcp_servers(self) -> List[str]:
        """
        Get a list of available MCP servers.
        
        Returns:
            List of MCP server names
        """
        try:
            from ..config import Config
            return Config.get_available_mcp_servers()
        except Exception as e:
            logger.error(f"Failed to get available MCP servers: {e}")
            return []
    
class TemplateBasedAgentCreationTool(BaseTool):
    """Tool for creating agents based on templates."""
    
    def __init__(self, agent_factory):
        """
        Initialize the template-based agent creation tool.
        
        Args:
            agent_factory: Factory for creating agents
        """
        self.agent_factory = agent_factory
        self.templates = self._load_templates()
        
        super().__init__(
            name="create_agent_from_template",
            description="Creates a new agent based on a predefined template",
            parameters={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "ID of the template to use"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the agent to create"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional custom description (defaults to template description)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional custom model (defaults to template model)"
                    },
                    "customizations": {
                        "type": "object",
                        "description": "Additional customizations for the template"
                    }
                },
                "required": ["template_id", "name"]
            }
        )
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load predefined agent templates.
        
        Returns:
            Dictionary of templates
        """
        # In a real implementation, these would be loaded from a file or database
        return {
            "writer": {
                "name": "Creative Writer",
                "description": "An agent specialized in creative writing and content creation",
                "skills": ["creative_writing", "storytelling", "content_creation"],
                "model": "claude-3-opus-20240229",
                "category": "creative",
                "examples": [
                    ["Write a short story about a robot discovering emotions"],
                    ["Create a blog post about sustainable travel"],
                    ["Draft a product description for a new smartphone"]
                ]
            },
            "analyst": {
                "name": "Data Analyst",
                "description": "An agent specialized in data analysis and visualization",
                "skills": ["data_analysis", "statistics", "visualization"],
                "model": "gemini-2.0-pro",
                "category": "analysis",
                "mcp_servers": ["postgres", "s3"],
                "examples": [
                    ["Analyze this CSV data and find trends"],
                    ["Calculate the correlation between these variables"],
                    ["Create a visualization of this dataset"]
                ]
            },
            "coder": {
                "name": "Code Assistant",
                "description": "An agent specialized in software development and code assistance",
                "skills": ["programming", "code_review", "debugging"],
                "model": "claude-3-opus-20240229",
                "category": "development",
                "mcp_servers": ["git", "github", "vscode"],
                "examples": [
                    ["Write a Python function to sort a list of dictionaries"],
                    ["Review this code for security vulnerabilities"],
                    ["Help me debug this JavaScript error"]
                ]
            },
            "researcher": {
                "name": "Research Assistant",
                "description": "An agent specialized in research and information gathering",
                "skills": ["research", "summarization", "fact_checking"],
                "model": "gemini-2.0-pro",
                "category": "knowledge",
                "examples": [
                    ["Research the impact of climate change on agriculture"],
                    ["Summarize the latest findings on quantum computing"],
                    ["Find credible sources about the history of artificial intelligence"]
                ]
            },
            "assistant": {
                "name": "Personal Assistant",
                "description": "An agent specialized in task management and personal assistance",
                "skills": ["task_management", "scheduling", "reminders"],
                "model": "gemini-2.0-flash",
                "category": "productivity",
                "examples": [
                    ["Remind me to call John tomorrow at 3 PM"],
                    ["Schedule a meeting with the team next week"],
                    ["Help me plan my vacation to Europe"]
                ]
            }
        }
    
    def run(
        self,
        template_id: str,
        name: str,
        description: Optional[str] = None,
        model: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent based on a template.
        
        Args:
            template_id: ID of the template to use
            name: Name of the agent
            description: Optional custom description
            model: Optional custom model
            customizations: Additional customizations
            
        Returns:
            Dict containing the new agent's information
        """
        try:
            # Check if the template exists
            if template_id not in self.templates:
                return {
                    "status": "error",
                    "message": f"Template with ID '{template_id}' not found",
                    "available_templates": list(self.templates.keys())
                }
            
            # Get the template
            template = self.templates[template_id]
            
            # Create agent parameters
            agent_params = template.copy()
            agent_params["name"] = name
            
            # Override with custom values if provided
            if description:
                agent_params["description"] = description
            if model:
                agent_params["model"] = model
            
            # Apply additional customizations
            if customizations:
                for key, value in customizations.items():
                    if key not in ["name", "template_id"]:
                        agent_params[key] = value
            
            # Create the agent
            agent_info = self.agent_factory.create_agent(
                name=agent_params["name"],
                description=agent_params["description"],
                skills=agent_params["skills"],
                model=agent_params["model"],
                instructions=agent_params.get("instructions"),
                mcp_servers=agent_params.get("mcp_servers"),
                metadata={
                    "template_id": template_id,
                    "category": agent_params.get("category"),
                    "examples": agent_params.get("examples")
                }
            )
            
            return {
                "status": "success",
                "message": f"Agent '{name}' created successfully from template '{template_id}'",
                "agent_id": agent_info["id"],
                "agent_details": agent_info
            }
        except Exception as e:
            logger.error(f"Failed to create agent from template '{template_id}': {e}")
            return {
                "status": "error",
                "message": f"Failed to create agent from template: {str(e)}"
            }
    
    def list_templates(self) -> Dict[str, Any]:
        """
        List all available templates.
        
        Returns:
            Dict containing template information
        """
        template_summaries = {}
        for template_id, template in self.templates.items():
            template_summaries[template_id] = {
                "name": template["name"],
                "description": template["description"],
                "skills": template["skills"],
                "category": template.get("category", "general")
            }
        
        return {
            "status": "success",
            "templates": template_summaries
        }
