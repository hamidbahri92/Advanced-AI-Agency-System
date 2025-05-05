#!/usr/bin/env python3
"""
Main entry point for the AI Agency System.
"""

import os
import argparse
import asyncio
from pathlib import Path

from agency.config import Config
from agency.agent_registry import AgentRegistry
from agency.agent_factory import AgentFactory
from agency.parent_agent import ParentAgent
from agency.communication.a2a_server import A2AServer
from agency.communication.mcp_integration import MCPServerManager
from agency.api.server import APIServer
from agency.utils.logging import get_logger

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI Agency System")
    
    parser.add_argument(
        "--host",
        type=str,
        default=Config.SERVER_HOST,
        help=f"Host to bind to (default: {Config.SERVER_HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=Config.SERVER_PORT,
        help=f"Port to listen on (default: {Config.SERVER_PORT})"
    )
    
    parser.add_argument(
        "--mcp-config",
        type=str,
        default=str(Config.MCP_CONFIG_PATH),
        help=f"Path to MCP configuration file (default: {Config.MCP_CONFIG_PATH})"
    )
    
    parser.add_argument(
        "--registry-path",
        type=str,
        default=str(Config.REGISTRY_PATH),
        help=f"Path to agent registry file (default: {Config.REGISTRY_PATH})"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    return parser.parse_args()

async def async_main(args):
    """
    Asynchronous main function.
    
    Args:
        args: Command line arguments
    """
    try:
        # Set up configuration
        Config.LOG_LEVEL = getattr(logging, args.log_level)
        Config.MCP_CONFIG_PATH = Path(args.mcp_config)
        Config.REGISTRY_PATH = Path(args.registry_path)
        
        # Load MCP configuration
        Config.load_mcp_config()
        
        # Initialize components
        logger.info("Initializing AI Agency System")
        
        # Create MCP server manager
        logger.info("Creating MCP server manager")
        mcp_manager = MCPServerManager(Config.MCP_CONFIG_PATH)
        
        # Create agent registry
        logger.info("Creating agent registry")
        registry = AgentRegistry(Config.REGISTRY_PATH)
        
        # Create agent factory
        logger.info("Creating agent factory")
        agent_factory = AgentFactory(registry, mcp_manager)
        
        # Create parent agent
        logger.info("Creating parent agent")
        parent_agent = ParentAgent(registry, agent_factory, mcp_manager)
        
        # Create A2A server
        logger.info("Creating A2A server")
        a2a_server = A2AServer(registry, agent_factory)
        a2a_server.setup_routes()
        
        # Create API server
        logger.info("Creating API server")
        api_server = APIServer(
            registry=registry,
            agent_factory=agent_factory,
            parent_agent=parent_agent,
            mcp_manager=mcp_manager,
            a2a_server=a2a_server
        )
        
        # Start the server
        logger.info(f"Starting server on {args.host}:{args.port}")
        api_server.run(host=args.host, port=args.port)
    except Exception as e:
        logger.error(f"Error in async_main: {e}")
        raise

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    import logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the asynchronous main function
    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
