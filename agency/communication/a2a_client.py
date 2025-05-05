import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, AsyncGenerator
import httpx
from httpx_sse import aconnect_sse

from ..utils.logging import get_logger

logger = get_logger(__name__)

class A2AClient:
    """
    Client for communicating with agents using the A2A protocol.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the A2A client.
        
        Args:
            base_url: Base URL of the agent's A2A endpoint
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Retrieve the agent's card.
        
        Returns:
            Agent card dictionary
        """
        well_known_url = f"{self.base_url}/.well-known/agent.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(well_known_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def send_message(
        self,
        message: str,
        task_id: Optional[str] = None,
        stream: bool = False,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send a message to the agent.
        
        Args:
            message: Message text to send
            task_id: Optional ID for an existing task
            stream: Whether to stream the response
            callback: Optional callback for handling streamed responses
        
        Returns:
            Either the complete response or an async generator for streamed responses
        """
        # Generate a task ID if none is provided
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Create the message part
        message_part = {
            "type": "text",
            "text": message
        }
        
        # Create the request payload
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/sendSubscribe" if stream else "tasks/send",
            "params": {
                "task_id": task_id,
                "message": {
                    "role": "user",
                    "parts": [message_part]
                }
            },
            "id": str(uuid.uuid4())
        }
        
        # Set up headers
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        if stream:
            return self._stream_response(payload, headers, callback)
        else:
            return await self._send_request(payload, headers)
    
    async def _send_request(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Send a non-streaming request to the agent.
        
        Args:
            payload: Request payload
            headers: Request headers
        
        Returns:
            Agent response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _stream_response(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the response from the agent.
        
        Args:
            payload: Request payload
            headers: Request headers
            callback: Optional callback for handling events
        
        Yields:
            Server-sent events
        """
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(client, "POST", self.base_url, json=payload, headers=headers) as event_source:
                async for event in event_source.aiter_sse():
                    if event.data:
                        try:
                            data = json.loads(event.data)
                            if callback:
                                callback(data)
                            yield data
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode SSE data: {event.data}")
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get information about a task.
        
        Args:
            task_id: ID of the task
        
        Returns:
            Task information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {
                "task_id": task_id
            },
            "id": str(uuid.uuid4())
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        return await self._send_request(payload, headers)
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
        
        Returns:
            Result of the cancellation
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/cancel",
            "params": {
                "task_id": task_id
            },
            "id": str(uuid.uuid4())
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        return await self._send_request(payload, headers)
    
    async def send_file(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        task_id: Optional[str] = None,
        message: Optional[str] = None,
        stream: bool = False,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send a file to the agent.
        
        Args:
            file_content: Content of the file as bytes
            file_name: Name of the file
            mime_type: MIME type of the file
            task_id: Optional ID for an existing task
            message: Optional message text to send with the file
            stream: Whether to stream the response
            callback: Optional callback for handling streamed responses
        
        Returns:
            Either the complete response or an async generator for streamed responses
        """
        # Generate a task ID if none is provided
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Create parts for the message
        parts = []
        
        # Add text part if message is provided
        if message:
            parts.append({
                "type": "text",
                "text": message
            })
        
        # Add file part
        import base64
        file_part = {
            "type": "file",
            "file": {
                "mime_type": mime_type,
                "file_name": file_name,
                "data": base64.b64encode(file_content).decode('utf-8')
            }
        }
        parts.append(file_part)
        
        # Create the request payload
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/sendSubscribe" if stream else "tasks/send",
            "params": {
                "task_id": task_id,
                "message": {
                    "role": "user",
                    "parts": parts
                }
            },
            "id": str(uuid.uuid4())
        }
        
        # Set up headers
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        if stream:
            return self._stream_response(payload, headers, callback)
        else:
            return await self._send_request(payload, headers)
    
    async def send_data(
        self,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
        message: Optional[str] = None,
        stream: bool = False,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send structured data to the agent.
        
        Args:
            data: Structured data to send
            task_id: Optional ID for an existing task
            message: Optional message text to send with the data
            stream: Whether to stream the response
            callback: Optional callback for handling streamed responses
        
        Returns:
            Either the complete response or an async generator for streamed responses
        """
        # Generate a task ID if none is provided
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Create parts for the message
        parts = []
        
        # Add text part if message is provided
        if message:
            parts.append({
                "type": "text",
                "text": message
            })
        
        # Add data part
        data_part = {
            "type": "data",
            "data": data
        }
        parts.append(data_part)
        
        # Create the request payload
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/sendSubscribe" if stream else "tasks/send",
            "params": {
                "task_id": task_id,
                "message": {
                    "role": "user",
                    "parts": parts
                }
            },
            "id": str(uuid.uuid4())
        }
        
        # Set up headers
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        if stream:
            return self._stream_response(payload, headers, callback)
        else:
            return await self._send_request(payload, headers)
    
    async def list_tasks(self) -> Dict[str, Any]:
        """
        List all tasks for the agent.
        
        Returns:
            Dictionary with task information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/list",
            "params": {},
            "id": str(uuid.uuid4())
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        return await self._send_request(payload, headers)
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dictionary with agent information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "agent/info",
            "params": {},
            "id": str(uuid.uuid4())
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        return await self._send_request(payload, headers)
    
    def set_api_key(self, api_key: str) -> None:
        """
        Set the API key for authentication.
        
        Args:
            api_key: API key to use
        """
        self.api_key = api_key
        self.headers["x-api-key"] = api_key
