import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request
from starlette.background import BackgroundTask
import uvicorn

from ..utils.logging import get_logger
from ..utils.security import verify_api_key
from ..config import Config

logger = get_logger(__name__)

class A2AServer:
    """
    Server for exposing agents via the A2A protocol.
    """
    
    def __init__(self, registry, agent_factory):
        """
        Initialize the A2A server.
        
        Args:
            registry: Agent registry for looking up agents
            agent_factory: Factory for managing agents
        """
        self.registry = registry
        self.agent_factory = agent_factory
        self.tasks = {}  # Store active tasks
        self.app = None  # Will be initialized in setup_routes
    
    def setup_routes(self):
        """Set up the routes for the server."""
        routes = [
            Route("/.well-known/agent.json", self.get_agency_card),
            Route("/agents/{agent_id}/.well-known/agent.json", self.get_agent_card),
            Route("/agents/{agent_id}", self.handle_agent_request, methods=["POST"]),
            Route("/agency", self.handle_agency_request, methods=["POST"]),
        ]
        
        self.app = Starlette(routes=routes)
        return self.app
    
    async def get_agency_card(self, request: Request) -> JSONResponse:
        """
        Handle requests for the agency's agent card.
        
        Args:
            request: HTTP request
        
        Returns:
            JSON response with the agency card
        """
        agency_card = {
            "agentFormat": "1.0.0",
            "info": {
                "id": "ai-agency",
                "name": "AI Agency",
                "description": "Autonomous AI Agency that can create and manage other agents",
                "version": "1.0.0",
                "contact": {
                    "name": "AI Agency",
                    "url": f"http://{request.base_url.hostname}:{request.base_url.port}/agency"
                }
            },
            "servers": [
                {
                    "url": f"http://{request.base_url.hostname}:{request.base_url.port}/agency",
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
                    "name": "agent_creation",
                    "description": "Create new specialized AI agents",
                    "examples": ["Create a data analysis agent", "Make an agent for customer support"]
                },
                {
                    "name": "agent_management",
                    "description": "Manage existing AI agents",
                    "examples": ["List all agents", "Update the weather agent"]
                },
                {
                    "name": "inter_agent_communication",
                    "description": "Facilitate communication between agents",
                    "examples": ["Ask the travel agent to book a flight", "Tell the weather agent to check Tokyo"]
                }
            ],
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_agent", "list_agents", "get_agent", "update_agent", "delete_agent", "communicate"],
                        "description": "The action to perform"
                    },
                    "agent_details": {
                        "type": "object",
                        "description": "Details for agent creation or updates",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the agent"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the agent's purpose"
                            },
                            "skills": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Skills the agent should have"
                            },
                            "model": {
                                "type": "string",
                                "description": "LLM model to use for the agent"
                            }
                        }
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent to interact with"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send to the agent"
                    }
                }
            }
        }
        
        return JSONResponse(agency_card)
    
    async def get_agent_card(self, request: Request) -> JSONResponse:
        """
        Handle requests for an agent's card.
        
        Args:
            request: HTTP request
        
        Returns:
            JSON response with the agent card
        """
        agent_id = request.path_params["agent_id"]
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            return JSONResponse(
                {"error": f"Agent with ID {agent_id} not found"},
                status_code=404
            )
        
        # Return the agent card from the path
        if "a2a_card_path" in agent:
            try:
                with open(agent["a2a_card_path"], 'r') as f:
                    agent_card = json.load(f)
                return JSONResponse(agent_card)
            except Exception as e:
                logger.error(f"Failed to load agent card for {agent_id}: {e}")
                return JSONResponse(
                    {"error": f"Failed to load agent card: {str(e)}"},
                    status_code=500
                )
        else:
            # Generate a card based on agent information
            agent_card = {
                "agentFormat": "1.0.0",
                "info": {
                    "id": agent_id,
                    "name": agent.get("name", "Agent"),
                    "description": agent.get("description", ""),
                    "version": agent.get("version", "1.0.0"),
                    "contact": {
                        "name": agent.get("name", "Agent"),
                        "url": f"http://{request.base_url.hostname}:{request.base_url.port}/agents/{agent_id}"
                    }
                },
                "servers": [
                    {
                        "url": f"http://{request.base_url.hostname}:{request.base_url.port}/agents/{agent_id}",
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
                    for skill in agent.get("skills", [])
                ]
            }
            
            return JSONResponse(agent_card)
    
    async def handle_agent_request(self, request: Request) -> Response:
        """
        Handle A2A requests for a specific agent.
        
        Args:
            request: HTTP request
        
        Returns:
            HTTP response
        """
        # Verify the API key
        if not verify_api_key(request):
            return JSONResponse(
                {"error": "Invalid or missing API key"},
                status_code=401
            )
        
        agent_id = request.path_params["agent_id"]
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            return JSONResponse(
                {"error": f"Agent with ID {agent_id} not found"},
                status_code=404
            )
        
        # Parse the request
        try:
            json_rpc = await request.json()
        except json.JSONDecodeError:
            return JSONResponse(
                {"error": "Invalid JSON"},
                status_code=400
            )
        
        # Process the request based on the method
        method = json_rpc.get("method")
        params = json_rpc.get("params", {})
        request_id = json_rpc.get("id")
        
        if not method or not request_id:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"},
                    "id": request_id
                },
                status_code=400
            )
        
        # Handle different A2A methods
        if method == "tasks/send":
            return await self._handle_tasks_send(request_id, params, agent)
        elif method == "tasks/sendSubscribe":
            return await self._handle_tasks_send_subscribe(request_id, params, agent)
        elif method == "tasks/get":
            return await self._handle_tasks_get(request_id, params)
        elif method == "tasks/cancel":
            return await self._handle_tasks_cancel(request_id, params)
        elif method == "tasks/list":
            return await self._handle_tasks_list(request_id, params)
        elif method == "agent/info":
            return await self._handle_agent_info(request_id, agent)
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                },
                status_code=404
            )
    
    async def handle_agency_request(self, request: Request) -> Response:
        """
        Handle A2A requests for the agency itself.
        
        Args:
            request: HTTP request
        
        Returns:
            HTTP response
        """
        # Verify the API key
        if not verify_api_key(request):
            return JSONResponse(
                {"error": "Invalid or missing API key"},
                status_code=401
            )
        
        # Parse the request
        try:
            json_rpc = await request.json()
        except json.JSONDecodeError:
            return JSONResponse(
                {"error": "Invalid JSON"},
                status_code=400
            )
        
        # Process the request based on the method
        method = json_rpc.get("method")
        params = json_rpc.get("params", {})
        request_id = json_rpc.get("id")
        
        if not method or not request_id:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"},
                    "id": request_id
                },
                status_code=400
            )
        
        # Handle different A2A methods
        if method == "tasks/send":
            return await self._handle_agency_tasks_send(request_id, params)
        elif method == "tasks/sendSubscribe":
            return await self._handle_agency_tasks_send_subscribe(request_id, params)
        elif method == "tasks/get":
            return await self._handle_tasks_get(request_id, params)
        elif method == "tasks/cancel":
            return await self._handle_tasks_cancel(request_id, params)
        elif method == "tasks/list":
            return await self._handle_tasks_list(request_id, params)
        elif method == "agent/info":
            return await self._handle_agency_info(request_id)
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                },
                status_code=404
            )
    
    async def _handle_tasks_send(self, request_id: str, params: Dict[str, Any], agent: Dict[str, Any]) -> JSONResponse:
        """
        Handle the tasks/send method for an agent.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
            agent: Agent information
        
        Returns:
            JSON response
        """
        # In a real implementation, this would process the message through the agent
        # For now, we'll provide a more sophisticated mock response
        
        task_id = params.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
        
        message = params.get("message", {})
        
        # Extract message content
        message_text = ""
        file_parts = []
        data_parts = []
        
        for part in message.get("parts", []):
            if part.get("type") == "text":
                message_text += part.get("text", "")
            elif part.get("type") == "file":
                file_parts.append(part.get("file", {}))
            elif part.get("type") == "data":
                data_parts.append(part.get("data", {}))
        
        # Create a task
        task = {
            "id": task_id,
            "state": "completed",
            "messages": [
                message,
                {
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "text": self._generate_agent_response(agent, message_text, file_parts, data_parts)
                        }
                    ]
                }
            ],
            "artifacts": []
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Return the response
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": task,
            "id": request_id
        })
    
    async def _handle_tasks_send_subscribe(self, request_id: str, params: Dict[str, Any], agent: Dict[str, Any]) -> Response:
        """
        Handle the tasks/sendSubscribe method for an agent.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
            agent: Agent information
        
        Returns:
            SSE response
        """
        task_id = params.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
        
        message = params.get("message", {})
        
        # Extract message content
        message_text = ""
        file_parts = []
        data_parts = []
        
        for part in message.get("parts", []):
            if part.get("type") == "text":
                message_text += part.get("text", "")
            elif part.get("type") == "file":
                file_parts.append(part.get("file", {}))
            elif part.get("type") == "data":
                data_parts.append(part.get("data", {}))
        
        # Create the initial task
        task = {
            "id": task_id,
            "state": "working",
            "messages": [message],
            "artifacts": []
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Create the SSE response
        async def stream_response():
            # Send the initial task
            yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': task, 'id': request_id})}\n\n"
            await asyncio.sleep(0.5)
            
            # Generate the response
            response_text = self._generate_agent_response(agent, message_text, file_parts, data_parts)
            
            # Stream response in chunks
            chunks = self._chunk_text(response_text, 50)  # ~50 chars per chunk
            
            for i, chunk in enumerate(chunks):
                # Update the task with the chunk
                if i == 0:
                    # First chunk - add a new message
                    task["messages"].append({
                        "role": "agent",
                        "parts": [
                            {
                                "type": "text",
                                "text": chunk
                            }
                        ]
                    })
                else:
                    # Subsequent chunks - update the existing message
                    task["messages"][-1]["parts"][0]["text"] += chunk
                
                # If it's the last chunk, mark as completed
                if i == len(chunks) - 1:
                    task["state"] = "completed"
                
                # Send the update
                yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': task, 'id': request_id})}\n\n"
                await asyncio.sleep(0.2)  # Simulate typing delay
        
        return Response(
            stream_response(),
            media_type="text/event-stream"
        )
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks of approximately the given size.
        
        Args:
            text: Text to split
            chunk_size: Approximate size of each chunk
        
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def _handle_agency_tasks_send(self, request_id: str, params: Dict[str, Any]) -> JSONResponse:
        """
        Handle the tasks/send method for the agency itself.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
        
        Returns:
            JSON response
        """
        task_id = params.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
        
        message = params.get("message", {})
        
        # Extract message content
        message_text = ""
        file_parts = []
        data_parts = []
        
        for part in message.get("parts", []):
            if part.get("type") == "text":
                message_text += part.get("text", "")
            elif part.get("type") == "file":
                file_parts.append(part.get("file", {}))
            elif part.get("type") == "data":
                data_parts.append(part.get("data", {}))
        
        # Generate an agency response based on the message
        response_text = self._generate_agency_response(message_text, file_parts, data_parts)
        
        # Create a task
        task = {
            "id": task_id,
            "state": "completed",
            "messages": [
                message,
                {
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ]
                }
            ],
            "artifacts": []
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Return the response
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": task,
            "id": request_id
        })
    
    async def _handle_agency_tasks_send_subscribe(self, request_id: str, params: Dict[str, Any]) -> Response:
        """
        Handle the tasks/sendSubscribe method for the agency.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
        
        Returns:
            SSE response
        """
        task_id = params.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
        
        message = params.get("message", {})
        
        # Extract message content
        message_text = ""
        file_parts = []
        data_parts = []
        
        for part in message.get("parts", []):
            if part.get("type") == "text":
                message_text += part.get("text", "")
            elif part.get("type") == "file":
                file_parts.append(part.get("file", {}))
            elif part.get("type") == "data":
                data_parts.append(part.get("data", {}))
        
        # Create the initial task
        task = {
            "id": task_id,
            "state": "working",
            "messages": [message],
            "artifacts": []
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Create the SSE response
        async def stream_response():
            # Send the initial task
            yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': task, 'id': request_id})}\n\n"
            await asyncio.sleep(0.5)
            
            # Generate the response
            response_text = self._generate_agency_response(message_text, file_parts, data_parts)
            
            # Stream response in chunks
            chunks = self._chunk_text(response_text, 50)  # ~50 chars per chunk
            
            for i, chunk in enumerate(chunks):
                # Update the task with the chunk
                if i == 0:
                    # First chunk - add a new message
                    task["messages"].append({
                        "role": "agent",
                        "parts": [
                            {
                                "type": "text",
                                "text": chunk
                            }
                        ]
                    })
                else:
                    # Subsequent chunks - update the existing message
                    task["messages"][-1]["parts"][0]["text"] += chunk
                
                # If it's the last chunk, mark as completed
                if i == len(chunks) - 1:
                    task["state"] = "completed"
                
                # Send the update
                yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': task, 'id': request_id})}\n\n"
                await asyncio.sleep(0.2)  # Simulate typing delay
        
        return Response(
            stream_response(),
            media_type="text/event-stream"
        )
    
    async def _handle_tasks_get(self, request_id: str, params: Dict[str, Any]) -> JSONResponse:
        """
        Handle the tasks/get method.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
        
        Returns:
            JSON response
        """
        task_id = params.get("task_id")
        if not task_id or task_id not in self.tasks:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task with ID {task_id} not found"},
                "id": request_id
            }, status_code=404)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": self.tasks[task_id],
            "id": request_id
        })
    
    async def _handle_tasks_cancel(self, request_id: str, params: Dict[str, Any]) -> JSONResponse:
        """
        Handle the tasks/cancel method.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
        
        Returns:
            JSON response
        """
        task_id = params.get("task_id")
        if not task_id or task_id not in self.tasks:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task with ID {task_id} not found"},
                "id": request_id
            }, status_code=404)
        
        # Update the task state to canceled
        self.tasks[task_id]["state"] = "canceled"
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": self.tasks[task_id],
            "id": request_id
        })
    
    async def _handle_tasks_list(self, request_id: str, params: Dict[str, Any]) -> JSONResponse:
        """
        Handle the tasks/list method.
        
        Args:
            request_id: JSON-RPC request ID
            params: Method parameters
        
        Returns:
            JSON response
        """
        # Get task summaries (without full message content)
        task_summaries = []
        for task_id, task in self.tasks.items():
            summary = {
                "id": task_id,
                "state": task["state"],
                "message_count": len(task["messages"]),
                "created_at": task.get("created_at", ""),
                "updated_at": task.get("updated_at", "")
            }
            task_summaries.append(summary)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {"tasks": task_summaries},
            "id": request_id
        })
    
    async def _handle_agent_info(self, request_id: str, agent: Dict[str, Any]) -> JSONResponse:
        """
        Handle the agent/info method.
        
        Args:
            request_id: JSON-RPC request ID
            agent: Agent information
        
        Returns:
            JSON response
        """
        # Return agent information
        info = {
            "id": agent.get("id", ""),
            "name": agent.get("name", ""),
            "description": agent.get("description", ""),
            "skills": agent.get("skills", []),
            "status": agent.get("status", "active"),
            "created_at": agent.get("created_at", ""),
            "updated_at": agent.get("updated_at", "")
        }
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": info,
            "id": request_id
        })
    
    async def _handle_agency_info(self, request_id: str) -> JSONResponse:
        """
        Handle the agent/info method for the agency.
        
        Args:
            request_id: JSON-RPC request ID
        
        Returns:
            JSON response
        """
        # Return agency information
        info = {
            "id": "ai-agency",
            "name": "AI Agency",
            "description": "Autonomous AI Agency that can create and manage other agents",
            "skills": [
                "agent_creation",
                "agent_management",
                "inter_agent_communication"
            ],
            "agent_count": len(self.registry.list_agents()),
            "version": "1.0.0"
        }
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": info,
            "id": request_id
        })
    
    def _generate_agent_response(self, agent: Dict[str, Any], message_text: str, file_parts: List[Dict[str, Any]], data_parts: List[Dict[str, Any]]) -> str:
        """
        Generate a mock response from an agent.
        
        Args:
            agent: Agent information
            message_text: Message text
            file_parts: File parts from the message
            data_parts: Data parts from the message
        
        Returns:
            Generated response text
        """
        # In a real implementation, this would interact with the actual agent
        agent_name = agent.get("name", "Agent")
        agent_description = agent.get("description", "")
        agent_skills = agent.get("skills", [])
        
        # Build a response based on the agent's info and message
        if "create" in message_text.lower() and "agent" in message_text.lower():
            return f"I'm {agent_name}. I'd be happy to help with creating a new agent. Please provide details like the name, description, and skills for the new agent."
        
        if "list" in message_text.lower() and "agent" in message_text.lower():
            return f"I'm {agent_name}. I can list all available agents. Currently, there are {len(self.registry.list_agents())} agents registered in the system."
        
        if "file" in message_text.lower() and file_parts:
            return f"I'm {agent_name}. I received your file{' ' + file_parts[0].get('file_name', '') if file_parts[0].get('file_name') else ''}. I'll process it according to my capabilities: {', '.join(agent_skills)}."
        
        if "data" in message_text.lower() and data_parts:
            return f"I'm {agent_name}. I received your structured data. I'll analyze it based on my expertise in: {', '.join(agent_skills)}."
        
        # Default response
        return f"I'm {agent_name}, specialized in {', '.join(agent_skills)}. {agent_description} How can I assist you today?"
    
    def _generate_agency_response(self, message_text: str, file_parts: List[Dict[str, Any]], data_parts: List[Dict[str, Any]]) -> str:
        """
        Generate a mock response from the agency.
        
        Args:
            message_text: Message text
            file_parts: File parts from the message
            data_parts: Data parts from the message
        
        Returns:
            Generated response text
        """
        if "create" in message_text.lower() and "agent" in message_text.lower():
            return (
                "I am the AI Agency. I can help you create a new agent. "
                "To create an agent, I need the following information:\n"
                "- Name for the agent\n"
                "- Description of its purpose\n"
                "- List of skills it should have\n"
                "- (Optional) Specific model to use"
            )
        
        if "list" in message_text.lower() and "agent" in message_text.lower():
            agents = self.registry.list_agents()
            if agents:
                agent_list = "\n".join([f"- {agent['name']}: {agent['description']}" for agent in agents[:5]])
                return f"Here are the available agents:\n{agent_list}\n\nThere are {len(agents)} agents in total."
            else:
                return "There are no agents currently registered in the system."
        
        if "file" in message_text.lower() and file_parts:
            return f"I received your file{' ' + file_parts[0].get('file_name', '') if file_parts[0].get('file_name') else ''}. How would you like me to process it? I can create specialized agents for handling this type of data."
        
        if "data" in message_text.lower() and data_parts:
            return "I received your structured data. I can create specialized agents for analyzing this kind of information or forward it to an existing agent. What would you like to do?"
        
        # Default response
        return (
            "I am the AI Agency. I can help you create and manage AI agents. "
            "My capabilities include:\n"
            "- Creating specialized agents for specific tasks\n"
            "- Managing existing agents (listing, updating, deleting)\n"
            "- Facilitating communication between agents\n\n"
            "How can I assist you today?"
        )
    
    def run(self, host: str, port: int):
        """
        Run the A2A server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        if self.app is None:
            self.setup_routes()
        
        uvicorn.run(self.app, host=host, port=port)
