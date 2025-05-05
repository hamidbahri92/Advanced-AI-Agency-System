from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field

from ...utils.logging import get_logger
from ..middleware.auth import get_current_user, admin_required

logger = get_logger(__name__)

# Request and response models
class CreateAgentRequest(BaseModel):
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    skills: List[str] = Field(..., description="List of skills the agent should have")
    model: Optional[str] = Field(None, description="LLM model to use (optional)")
    instructions: Optional[str] = Field(None, description="Specific instructions for the agent (optional)")
    mcp_servers: Optional[List[str]] = Field(None, description="List of MCP servers to connect to (optional)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the agent (optional)")
    examples: Optional[List[List[str]]] = Field(None, description="Example queries for each skill (optional)")
    category: Optional[str] = Field(None, description="Category of the agent (optional)")

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = Field(None, description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent's purpose")
    skills: Optional[List[str]] = Field(None, description="List of skills the agent should have")
    model: Optional[str] = Field(None, description="LLM model to use")
    instructions: Optional[str] = Field(None, description="Specific instructions for the agent")
    mcp_servers: Optional[List[str]] = Field(None, description="List of MCP servers to connect to")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the agent")
    status: Optional[str] = Field(None, description="Status of the agent (e.g., 'active', 'inactive')")
    examples: Optional[List[List[str]]] = Field(None, description="Example queries for each skill")
    category: Optional[str] = Field(None, description="Category of the agent")

class MessageAgentRequest(BaseModel):
    message: str = Field(..., description="Message to send to the agent")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")

class AgentResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    skills: List[str] = Field(..., description="List of skills the agent has")
    model: str = Field(..., description="LLM model used by the agent")
    status: str = Field(..., description="Status of the agent")
    created_at: str = Field(..., description="Timestamp when the agent was created")
    updated_at: str = Field(..., description="Timestamp when the agent was last updated")

class AgentListResponse(BaseModel):
    count: int = Field(..., description="Number of agents")
    agents: List[AgentResponse] = Field(..., description="List of agents")

class MessageResponse(BaseModel):
    agent_id: str = Field(..., description="ID of the agent")
    agent_name: str = Field(..., description="Name of the agent")
    response: str = Field(..., description="Response from the agent")

def create_router(dependencies: Dict[str, Any]) -> APIRouter:
    """
    Create a router for agent-related endpoints.
    
    Args:
        dependencies: Dictionary of dependencies
    
    Returns:
        FastAPI router
    """
    router = APIRouter()
    
    registry = dependencies["registry"]
    agent_factory = dependencies["agent_factory"]
    parent_agent = dependencies["parent_agent"]
    
    @router.post(
        "/",
        response_model=AgentResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a new agent"
    )
    async def create_agent(
        request: CreateAgentRequest,
        current_user = Depends(get_current_user)
    ):
        """Create a new agent with the specified parameters."""
        try:
            # Create the agent
            agent_info = agent_factory.create_agent(
                name=request.name,
                description=request.description,
                skills=request.skills,
                model=request.model,
                instructions=request.instructions,
                mcp_servers=request.mcp_servers,
                metadata={
                    **(request.metadata or {}),
                    "created_by": current_user.get("username"),
                    "category": request.category,
                    "examples": request.examples
                }
            )
            
            return agent_info
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create agent: {str(e)}"
            )
    
    @router.get(
        "/",
        response_model=AgentListResponse,
        summary="List all agents",
        description="List all agents, optionally filtered by various criteria"
    )
    async def list_agents(
        skill: Optional[str] = Query(None, description="Filter by skill"),
        status: Optional[str] = Query(None, description="Filter by status"),
        model: Optional[str] = Query(None, description="Filter by model"),
        category: Optional[str] = Query(None, description="Filter by category"),
        search: Optional[str] = Query(None, description="Search by name, description, or skills"),
        limit: int = Query(100, description="Maximum number of agents to return"),
        offset: int = Query(0, description="Number of agents to skip")
    ):
        """List all agents, optionally filtered by various criteria."""
        try:
            # Apply filters
            if skill:
                agents = registry.get_agents_by_skill(skill)
            elif status:
                agents = registry.get_agents_by_status(status)
            elif model:
                agents = registry.get_agents_by_model(model)
            elif category:
                agents = registry.get_agents_by_category(category)
            elif search:
                agents = registry.search_agents(search)
            else:
                agents = registry.list_agents()
            
            # Apply pagination
            total = len(agents)
            agents = agents[offset:offset + limit]
            
            return {
                "count": total,
                "agents": agents
            }
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list agents: {str(e)}"
            )
    
    @router.get(
        "/{agent_id}",
        response_model=AgentResponse,
        summary="Get agent details",
        description="Get detailed information about a specific agent"
    )
    async def get_agent(
        agent_id: str = Path(..., description="ID of the agent")
    ):
        """Get detailed information about a specific agent."""
        agent = registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' not found"
            )
        
        return agent
    
    @router.put(
        "/{agent_id}",
        response_model=AgentResponse,
        summary="Update agent",
        description="Update an existing agent"
    )
    async def update_agent(
        request: UpdateAgentRequest,
        agent_id: str = Path(..., description="ID of the agent"),
        current_user = Depends(get_current_user)
    ):
        """Update an existing agent."""
        try:
            # Create updates dictionary
            updates = {k: v for k, v in request.dict().items() if v is not None}
            
            # Add updater info
            updates["updated_by"] = current_user.get("username")
            
            # Update the agent
            updated_agent = agent_factory.update_agent(agent_id, updates)
            if not updated_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with ID '{agent_id}' not found"
                )
            
            return updated_agent
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update agent: {str(e)}"
            )
    
    @router.delete(
        "/{agent_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete agent",
        description="Delete an existing agent"
    )
    async def delete_agent(
        agent_id: str = Path(..., description="ID of the agent"),
        current_user = Depends(admin_required)
    ):
        """Delete an existing agent."""
        try:
            # Delete the agent
            success = agent_factory.delete_agent(agent_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with ID '{agent_id}' not found"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete agent: {str(e)}"
            )
    
    @router.post(
        "/{agent_id}/message",
        response_model=MessageResponse,
        summary="Send message to agent",
        description="Send a message to an agent and get their response"
    )
    async def message_agent(
        request: MessageAgentRequest,
        agent_id: str = Path(..., description="ID of the agent")
    ):
        """Send a message to an agent and get their response."""
        try:
            # Get the agent
            agent = registry.get_agent(agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with ID '{agent_id}' not found"
                )
            
            # Send the message and get response
            response = await parent_agent.get_agent_response(agent_id, request.message)
            
            return {
                "agent_id": agent_id,
                "agent_name": agent.get("name", "Agent"),
                "response": response
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send message to agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message to agent: {str(e)}"
            )
    
    @router.post(
        "/{agent_id}/activate",
        response_model=AgentResponse,
        summary="Activate agent",
        description="Activate an inactive agent"
    )
    async def activate_agent(
        agent_id: str = Path(..., description="ID of the agent")
    ):
        """Activate an inactive agent."""
        try:
            # Activate the agent
            success = agent_factory.activate_agent(agent_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with ID '{agent_id}' not found"
                )
            
            # Get the updated agent
            agent = registry.get_agent(agent_id)
            return agent
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to activate agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to activate agent: {str(e)}"
            )
    
    @router.post(
        "/{agent_id}/deactivate",
        response_model=AgentResponse,
        summary="Deactivate agent",
        description="Deactivate an active agent"
    )
    async def deactivate_agent(
        agent_id: str = Path(..., description="ID of the agent")
    ):
        """Deactivate an active agent."""
        try:
            # Deactivate the agent
            success = agent_factory.deactivate_agent(agent_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with ID '{agent_id}' not found"
                )
            
            # Get the updated agent
            agent = registry.get_agent(agent_id)
            return agent
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate agent: {str(e)}"
            )
    
    return router
