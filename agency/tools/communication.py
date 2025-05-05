from typing import Dict, List, Any, Optional
import asyncio

from google.adk.tools import BaseTool

from ..utils.logging import get_logger
from ..communication.a2a_client import A2AClient
from ..config import Config

logger = get_logger(__name__)

class CommunicationTool(BaseTool):
    """Tool for communicating with other agents."""
    
    def __init__(self, registry):
        """
        Initialize the communication tool.
        
        Args:
            registry: Registry for looking up agents
        """
        self.registry = registry
        self.clients = {}  # Cache for A2A clients
        
        super().__init__(
            name="communicate_with_agent",
            description="Send a message to another agent and get their response",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent to communicate with"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send to the agent"
                    },
                    "stream": {
                        "type": "boolean",
                        "description": "Whether to stream the response (optional, defaults to false)"
                    },
                    "include_file": {
                        "type": "boolean",
                        "description": "Whether to include a file in the message (optional, defaults to false)"
                    },
                    "file_data": {
                        "type": "object",
                        "description": "File data to include (required if include_file is true)"
                    }
                },
                "required": ["agent_id", "message"]
            }
        )
    
    async def run(
        self,
        agent_id: str,
        message: str,
        stream: Optional[bool] = False,
        include_file: Optional[bool] = False,
        file_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an agent.
        
        Args:
            agent_id: ID of the agent to communicate with
            message: Message to send
            stream: Whether to stream the response
            include_file: Whether to include a file
            file_data: File data to include
            
        Returns:
            Dictionary with the agent's response
        """
        try:
            # Check if the agent exists
            agent = self.registry.get_agent(agent_id)
            if not agent:
                return {
                    "status": "error",
                    "message": f"Agent with ID '{agent_id}' not found"
                }
            
            # Get or create an A2A client for this agent
            client = self._get_client(agent_id)
            
            # Send the message
            if include_file and file_data:
                # Process file data
                file_content = file_data.get("content")
                file_name = file_data.get("name", "file.txt")
                mime_type = file_data.get("mime_type", "text/plain")
                
                # Ensure file_content is bytes
                if isinstance(file_content, str):
                    file_content = file_content.encode("utf-8")
                
                # Send message with file
                response = await client.send_file(
                    file_content=file_content,
                    file_name=file_name,
                    mime_type=mime_type,
                    message=message,
                    stream=stream
                )
            else:
                # Send text message
                response = await client.send_message(
                    message=message,
                    stream=stream
                )
            
            # Extract response text
            if not stream:
                # For non-streaming responses, extract text from the response
                if "result" in response and "messages" in response["result"]:
                    messages = response["result"]["messages"]
                    if len(messages) > 1 and "parts" in messages[-1]:
                        parts = messages[-1]["parts"]
                        for part in parts:
                            if part.get("type") == "text":
                                return {
                                    "status": "success",
                                    "agent_id": agent_id,
                                    "agent_name": agent.get("name", "Agent"),
                                    "response": part.get("text", "")
                                }
            
            # Return the raw response
            return {
                "status": "success",
                "agent_id": agent_id,
                "agent_name": agent.get("name", "Agent"),
                "response": str(response)
            }
        except Exception as e:
            logger.error(f"Error communicating with agent {agent_id}: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def _get_client(self, agent_id: str) -> A2AClient:
        """
        Get or create an A2A client for an agent.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            A2A client
        """
        if agent_id not in self.clients:
            self.clients[agent_id] = A2AClient(
                base_url=f"{Config.A2A_ENDPOINT}/agents/{agent_id}",
                api_key=Config.API_KEY
            )
        
        return self.clients[agent_id]

class MultiAgentCommunicationTool(BaseTool):
    """Tool for communicating with multiple agents simultaneously."""
    
    def __init__(self, registry):
        """
        Initialize the multi-agent communication tool.
        
        Args:
            registry: Registry for looking up agents
        """
        self.registry = registry
        self.clients = {}  # Cache for A2A clients
        
        super().__init__(
            name="communicate_with_multiple_agents",
            description="Send a message to multiple agents and get their responses",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to send to the agents"
                    },
                    "agent_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs of the agents to communicate with"
                    },
                    "filter_by_skill": {
                        "type": "string",
                        "description": "Alternatively, filter agents by skill"
                    },
                    "filter_by_category": {
                        "type": "string",
                        "description": "Alternatively, filter agents by category"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (optional, defaults to 30)"
                    }
                },
                "required": ["message"]
            }
        )
    
    async def run(
        self,
        message: str,
        agent_ids: Optional[List[str]] = None,
        filter_by_skill: Optional[str] = None,
        filter_by_category: Optional[str] = None,
        timeout: Optional[float] = 30.0
    ) -> Dict[str, Any]:
        """
        Send a message to multiple agents.
        
        Args:
            message: Message to send
            agent_ids: IDs of the agents to communicate with
            filter_by_skill: Filter agents by skill
            filter_by_category: Filter agents by category
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with the agents' responses
        """
        try:
            # Get agents based on parameters
            agents = []
            
            if agent_ids:
                # Get agents by IDs
                for agent_id in agent_ids:
                    agent = self.registry.get_agent(agent_id)
                    if agent:
                        agents.append(agent)
            elif filter_by_skill:
                # Get agents by skill
                agents = self.registry.get_agents_by_skill(filter_by_skill)
            elif filter_by_category:
                # Get agents by category
                agents = self.registry.get_agents_by_category(filter_by_category)
            else:
                # Get all active agents
                agents = self.registry.get_agents_by_status("active")
            
            if not agents:
                return {
                    "status": "error",
                    "message": "No matching agents found"
                }
            
            # Create tasks for each agent
            tasks = []
            for agent in agents:
                client = self._get_client(agent["id"])
                tasks.append(self._send_message_to_agent(client, agent, message))
            
            # Run tasks concurrently with timeout
            responses = {}
            try:
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=timeout,
                    return_when=asyncio.ALL_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    try:
                        result = task.result()
                        responses[result["agent_id"]] = {
                            "agent_name": result["agent_name"],
                            "response": result["response"]
                        }
                    except Exception as e:
                        logger.error(f"Error processing task result: {e}")
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            except asyncio.TimeoutError:
                logger.warning("Multi-agent communication timed out")
            
            return {
                "status": "success",
                "message": f"Communicated with {len(responses)} agents",
                "responses": responses
            }
        except Exception as e:
            logger.error(f"Error in multi-agent communication: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def _get_client(self, agent_id: str) -> A2AClient:
        """
        Get or create an A2A client for an agent.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            A2A client
        """
        if agent_id not in self.clients:
            self.clients[agent_id] = A2AClient(
                base_url=f"{Config.A2A_ENDPOINT}/agents/{agent_id}",
                api_key=Config.API_KEY
            )
        
        return self.clients[agent_id]
    
    async def _send_message_to_agent(
        self,
        client: A2AClient,
        agent: Dict[str, Any],
        message: str
    ) -> Dict[str, Any]:
        """
        Send a message to an agent and process the response.
        
        Args:
            client: A2A client
            agent: Agent information
            message: Message to send
            
        Returns:
            Dictionary with the agent's response
        """
        try:
            # Send the message
            response = await client.send_message(message)
            
            # Extract response text
            if "result" in response and "messages" in response["result"]:
                messages = response["result"]["messages"]
                if len(messages) > 1 and "parts" in messages[-1]:
                    parts = messages[-1]["parts"]
                    for part in parts:
                        if part.get("type") == "text":
                            return {
                                "agent_id": agent["id"],
                                "agent_name": agent.get("name", "Agent"),
                                "response": part.get("text", "")
                            }
            
            # Return the raw response
            return {
                "agent_id": agent["id"],
                "agent_name": agent.get("name", "Agent"),
                "response": str(response)
            }
        except Exception as e:
            logger.error(f"Error communicating with agent {agent['id']}: {e}")
            return {
                "agent_id": agent["id"],
                "agent_name": agent.get("name", "Agent"),
                "error": str(e)
            }
