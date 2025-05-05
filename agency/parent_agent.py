from typing import Dict, List, Any, Optional
import asyncio

from google.adk.agent import BaseAgent, Message
from google.adk.toolbox import ToolCall, Tool

from .config import Config
from .agent_registry import AgentRegistry
from .agent_factory import AgentFactory
from .communication.a2a_client import A2AClient
from .communication.mcp_integration import MCPServerManager
from .utils.logging import get_logger
from .tools.agent_creation import AgentCreationTool
from .tools.agent_management import AgentManagementTool
from .tools.communication import CommunicationTool

logger = get_logger(__name__)

class ParentAgent(BaseAgent):
    """
    Parent agent that can create and manage other agents.
    """
    
    def __init__(
        self, 
        registry: AgentRegistry, 
        factory: AgentFactory, 
        mcp_manager: MCPServerManager,
        model_id: Optional[str] = None
    ):
        """
        Initialize the parent agent.
        
        Args:
            registry: Registry for tracking agents
            factory: Factory for creating agents
            mcp_manager: Manager for MCP servers
            model_id: ID of the model to use
        """
        # Set up components
        self.registry = registry
        self.factory = factory
        self.mcp_manager = mcp_manager
        
        # Create tools
        tools = self._create_tools()
        
        # Get the model ID
        if not model_id:
            model_id = Config.DEFAULT_MODEL
        
        # Initialize the base agent
        super().__init__(
            model=model_id,
            tools=tools
        )
        
        # Set additional attributes
        self.agent_instances = {}  # Store active agent instances
        self.clients = {}  # Store A2A clients
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools for the parent agent.
        
        Returns:
            List of tools
        """
        tools = [
            AgentCreationTool(self.factory),
            AgentManagementTool(self.registry, self.factory),
            CommunicationTool(self.registry)
        ]
        
        # Add MCP tools if available
        for server_name, server in self.mcp_manager.mcp_servers.items():
            # Add server-specific tools
            server_tools = server.list_tools()
            for tool in server_tools:
                tools.append(tool)
        
        return tools
    
    async def process(self, message: Message) -> Message:
        """
        Process a message and generate a response.
        
        Args:
            message: Input message
        
        Returns:
            Response message
        """
        # Log the incoming message
        logger.info(f"Received message: {message.text[:100]}...")
        
        # Process the message using the base agent
        response = await super().process(message)
        
        # Log the response
        logger.info(f"Sending response: {response.text[:100]}...")
        
        return response
    
    async def handle_tool_call(self, tool_call: ToolCall) -> Any:
        """
        Handle a tool call from the agent.
        
        Args:
            tool_call: Tool call to handle
        
        Returns:
            Result of the tool call
        """
        tool_name = tool_call.name
        
        # Log the tool call
        logger.info(f"Handling tool call: {tool_name}")
        
        # Special handling for agent management
        if tool_name == "create_agent":
            # Create the agent
            result = await super().handle_tool_call(tool_call)
            
            # Create an A2A client for the new agent
            if result.get("status") == "success":
                agent_id = result.get("agent_id")
                self._create_a2a_client(agent_id)
            
            return result
        
        # Special handling for communication tool
        if tool_name == "communicate_with_agent":
            # Get parameters
            agent_id = tool_call.args.get("agent_id")
            message = tool_call.args.get("message")
            
            # Check if we have a client for this agent
            if agent_id not in self.clients:
                self._create_a2a_client(agent_id)
            
            # Send the message
            if agent_id in self.clients:
                client = self.clients[agent_id]
                response = await client.send_message(message)
                
                # Extract the response text
                if "result" in response and "messages" in response["result"]:
                    messages = response["result"]["messages"]
                    if len(messages) > 1 and "parts" in messages[-1]:
                        parts = messages[-1]["parts"]
                        for part in parts:
                            if part.get("type") == "text":
                                return {"response": part.get("text", "")}
                
                # Return the raw response if we couldn't extract text
                return {"response": str(response)}
            else:
                return {"error": f"Failed to create A2A client for agent {agent_id}"}
        
        # Default handling for other tools
        return await super().handle_tool_call(tool_call)
    
    def _create_a2a_client(self, agent_id: str) -> bool:
        """
        Create an A2A client for an agent.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            True if the client was created, False otherwise
        """
        try:
            # Get the agent information
            agent = self.registry.get_agent(agent_id)
            if not agent:
                logger.warning(f"Attempted to create A2A client for non-existent agent: {agent_id}")
                return False
            
            # Create the client
            client = A2AClient(
                base_url=f"{Config.A2A_ENDPOINT}/agents/{agent_id}",
                api_key=Config.API_KEY
            )
            
            # Store the client
            self.clients[agent_id] = client
            
            logger.info(f"Created A2A client for agent: {agent['name']} ({agent_id})")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create A2A client for agent {agent_id}: {e}")
            return False
    
    async def get_agent_response(self, agent_id: str, message: str) -> str:
        """
        Get a response from an agent.
        
        Args:
            agent_id: ID of the agent
            message: Message to send
        
        Returns:
            Agent's response
        
        Raises:
            ValueError: If the agent doesn't exist or if communication fails
        """
        # Ensure we have a client for this agent
        if agent_id not in self.clients:
            if not self._create_a2a_client(agent_id):
                raise ValueError(f"Failed to create A2A client for agent {agent_id}")
        
        # Get the client
        client = self.clients[agent_id]
        
        try:
            # Send the message
            response = await client.send_message(message)
            
            # Extract the response text
            if "result" in response and "messages" in response["result"]:
                messages = response["result"]["messages"]
                if len(messages) > 1 and "parts" in messages[-1]:
                    parts = messages[-1]["parts"]
                    for part in parts:
                        if part.get("type") == "text":
                            return part.get("text", "")
            
            # Return the raw response if we couldn't extract text
            return str(response)
        except Exception as e:
            logger.error(f"Failed to get response from agent {agent_id}: {e}")
            raise ValueError(f"Failed to communicate with agent {agent_id}: {str(e)}")
    
    async def create_agent_and_get_response(
        self,
        name: str,
        description: str,
        skills: List[str],
        message: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent and get a response from it.
        
        Args:
            name: Name of the agent
            description: Description of the agent
            skills: List of skills for the agent
            message: Message to send to the agent
            model: Optional model to use for the agent
        
        Returns:
            Dictionary with agent ID and response
        """
        # Create the agent
        agent_info = self.factory.create_agent(
            name=name,
            description=description,
            skills=skills,
            model=model
        )
        
        # Get the agent ID
        agent_id = agent_info["id"]
        
        # Get a response from the agent
        try:
            response = await self.get_agent_response(agent_id, message)
            
            return {
                "agent_id": agent_id,
                "response": response
            }
        except Exception as e:
            logger.error(f"Failed to get response from new agent {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "error": str(e)
            }
    
    async def handle_multi_agent_task(
        self,
        task_description: str,
        agent_selection_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a task using multiple agents.
        
        Args:
            task_description: Description of the task
            agent_selection_criteria: Criteria for selecting agents
        
        Returns:
            Dictionary with results from each agent
        """
        # Find suitable agents based on criteria
        agents = []
        
        # Check for skill requirement
        if "skill" in agent_selection_criteria:
            skill = agent_selection_criteria["skill"]
            agents.extend(self.registry.get_agents_by_skill(skill))
        
        # Check for category requirement
        if "category" in agent_selection_criteria and not agents:
            category = agent_selection_criteria["category"]
            agents.extend(self.registry.get_agents_by_category(category))
        
        # If no specific criteria matched or no agents found, use all active agents
        if not agents:
            agents = self.registry.get_active_agents()
        
        # Create tasks for each agent
        tasks = []
        for agent in agents:
            agent_id = agent["id"]
            
            # Ensure we have a client
            if agent_id not in self.clients:
                self._create_a2a_client(agent_id)
            
            if agent_id in self.clients:
                # Create a task to get a response from this agent
                task = self.get_agent_response(agent_id, task_description)
                tasks.append((agent_id, agent["name"], task))
        
        # Execute all tasks concurrently
        results = {}
        for agent_id, agent_name, task in tasks:
            try:
                response = await task
                results[agent_id] = {
                    "name": agent_name,
                    "response": response
                }
            except Exception as e:
                results[agent_id] = {
                    "name": agent_name,
                    "error": str(e)
                }
        
        return results
