from typing import Dict, List, Any, Optional
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from ..config import Config
from ..utils.logging import get_logger
from ..utils.security import verify_api_key
from .routes import agents, a2a, auth
from .middleware.auth import authenticate_request

logger = get_logger(__name__)

class APIServer:
    """
    FastAPI server for the AI Agency System.
    """
    
    def __init__(
        self,
        registry,
        agent_factory,
        parent_agent,
        mcp_manager,
        a2a_server
    ):
        """
        Initialize the API server.
        
        Args:
            registry: Agent registry
            agent_factory: Agent factory
            parent_agent: Parent agent
            mcp_manager: MCP server manager
            a2a_server: A2A server
        """
        self.registry = registry
        self.agent_factory = agent_factory
        self.parent_agent = parent_agent
        self.mcp_manager = mcp_manager
        self.a2a_server = a2a_server
        
        # Create the FastAPI app
        self.app = FastAPI(
            title="AI Agency API",
            description="API for managing an autonomous AI agency system",
            version="1.0.0"
        )
        
        # Set up CORS
        if Config.CORS_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=Config.CORS_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
        
        # Initialize routes
        self._init_routes()
    
    def _init_routes(self):
        """Initialize API routes."""
        # Inject dependencies
        dependencies = {
            "registry": self.registry,
            "agent_factory": self.agent_factory,
            "parent_agent": self.parent_agent,
            "mcp_manager": self.mcp_manager,
            "a2a_server": self.a2a_server
        }
        
        # Set up routes
        self.app.include_router(
            auth.create_router(dependencies),
            prefix="/auth",
            tags=["Authentication"]
        )
        
        self.app.include_router(
            agents.create_router(dependencies),
            prefix="/agents",
            tags=["Agents"],
            dependencies=[Security(authenticate_request)]
        )
        
        self.app.include_router(
            a2a.create_router(dependencies),
            prefix="/a2a",
            tags=["A2A"]
        )
        
        # Add root endpoint
        @self.app.get("/", tags=["Root"])
        async def root():
            return {
                "name": "AI Agency API",
                "version": "1.0.0",
                "status": "online"
            }
        
        # Add health check endpoint
        @self.app.get("/health", tags=["Health"])
        async def health():
            return {
                "status": "healthy",
                "components": {
                    "registry": "ok",
                    "agent_factory": "ok",
                    "parent_agent": "ok",
                    "mcp_manager": "ok",
                    "a2a_server": "ok"
                }
            }
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Run the API server.
        
        Args:
            host: Host to bind to (defaults to Config.SERVER_HOST)
            port: Port to listen on (defaults to Config.SERVER_PORT)
        """
        if host is None:
            host = Config.SERVER_HOST
        
        if port is None:
            port = Config.SERVER_PORT
        
        logger.info(f"Starting API server on {host}:{port}")
        
        # Run the server
        if Config.ENABLE_SSL and Config.SSL_CERT_FILE and Config.SSL_KEY_FILE:
            # Run with SSL
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                ssl_keyfile=Config.SSL_KEY_FILE,
                ssl_certfile=Config.SSL_CERT_FILE
            )
        else:
            # Run without SSL
            uvicorn.run(
                self.app,
                host=host,
                port=port
            )
