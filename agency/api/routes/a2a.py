from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from starlette.background import BackgroundTask

from ...utils.logging import get_logger

logger = get_logger(__name__)

def create_router(dependencies: Dict[str, Any]) -> APIRouter:
    """
    Create a router for A2A-related endpoints.
    
    Args:
        dependencies: Dictionary of dependencies
    
    Returns:
        FastAPI router
    """
    router = APIRouter()
    
    a2a_server = dependencies["a2a_server"]
    
    @router.get(
        "/.well-known/agent.json",
        summary="Get agency agent card",
        description="Get the agent card for the agency"
    )
    async def get_agency_card(request: Request):
        """Get the agent card for the agency."""
        return await a2a_server.get_agency_card(request)
    
    @router.get(
        "/agents/{agent_id}/.well-known/agent.json",
        summary="Get agent card",
        description="Get the agent card for a specific agent"
    )
    async def get_agent_card(request: Request):
        """Get the agent card for a specific agent."""
        return await a2a_server.get_agent_card(request)
    
    @router.post(
        "/agents/{agent_id}",
        summary="Handle agent request",
        description="Handle an A2A request for a specific agent"
    )
    async def handle_agent_request(request: Request):
        """Handle an A2A request for a specific agent."""
        return await a2a_server.handle_agent_request(request)
    
    @router.post(
        "/agency",
        summary="Handle agency request",
        description="Handle an A2A request for the agency itself"
    )
    async def handle_agency_request(request: Request):
        """Handle an A2A request for the agency itself."""
        return await a2a_server.handle_agency_request(request)
    
    return router
