#!/usr/bin/env python3
"""
Advanced AI Agency System example.

This example demonstrates a full-featured AI Agency with multiple specialized
agents, MCP integration, and A2A communication. It includes a simple API server
for interacting with the agency.
"""

import os
import asyncio
import argparse
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
    parser = argparse.ArgumentParser(description="Advanced AI Agency Example")
    
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
        default=None,
        help="Path to agent registry file (default: temporary file)"
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
    
    parser.add_argument(
        "--create-sample-agents",
        action="store_true",
        help="Create sample agents at startup"
    )
    
    return parser.parse_args()

async def create_sample_agents(agent_factory):
    """
    Create sample agents for demonstration purposes.
    
    Args:
        agent_factory: Agent factory for creating agents
    
    Returns:
        Dictionary mapping agent types to agent IDs
    """
    logger.info("Creating sample agents")
    
    agent_ids = {}
    
    # Writer agent
    writer_agent = agent_factory.create_agent(
        name="Creative Writer",
        description="An agent specialized in creative writing and content creation",
        skills=["creative_writing", "storytelling", "content_creation"],
        model="claude-3-opus-20240229",
        metadata={
            "category": "creative",
            "examples": [
                ["Write a short story about a robot discovering emotions"],
                ["Create a blog post about sustainable travel"],
                ["Draft a product description for a new smartphone"]
            ]
        }
    )
    agent_ids["writer"] = writer_agent["id"]
    logger.info(f"Created writer agent: {writer_agent['id']}")
    
    # Analyst agent
    analyst_agent = agent_factory.create_agent(
        name="Data Analyst",
        description="An agent specialized in data analysis and visualization",
        skills=["data_analysis", "statistics", "visualization"],
        model="gemini-2.0-pro",
        metadata={
            "category": "analysis",
            "examples": [
                ["Analyze this CSV data and find trends"],
                ["Calculate the correlation between these variables"],
                ["Create a visualization of this dataset"]
            ]
        }
    )
    agent_ids["analyst"] = analyst_agent["id"]
    logger.info(f"Created analyst agent: {analyst_agent['id']}")
    
    # Coder agent
    coder_agent = agent_factory.create_agent(
        name="Code Assistant",
        description="An agent specialized in software development and code assistance",
        skills=["programming", "code_review", "debugging"],
        model="claude-3-opus-20240229",
        metadata={
            "category": "development",
            "examples": [
                ["Write a Python function to sort a list of dictionaries"],
                ["Review this code for security vulnerabilities"],
                ["Help me debug this JavaScript error"]
            ]
        }
    )
    agent_ids["coder"] = coder_agent["id"]
    logger.info(f"Created coder agent: {coder_agent['id']}")
    
    # Researcher agent
    researcher_agent = agent_factory.create_agent(
        name="Research Assistant",
        description="An agent specialized in research and information gathering",
        skills=["research", "summarization", "fact_checking"],
        model="gemini-2.0-pro",
        metadata={
            "category": "knowledge",
            "examples": [
                ["Research the impact of climate change on agriculture"],
                ["Summarize the latest findings on quantum computing"],
                ["Find credible sources about the history of artificial intelligence"]
            ]
        }
    )
    agent_ids["researcher"] = researcher_agent["id"]
    logger.info(f"Created researcher agent: {researcher_agent['id']}")
    
    # Assistant agent
    assistant_agent = agent_factory.create_agent(
        name="Personal Assistant",
        description="An agent specialized in task management and personal assistance",
        skills=["task_management", "scheduling", "reminders"],
        model="gemini-2.0-flash",
        metadata={
            "category": "productivity",
            "examples": [
                ["Remind me to call John tomorrow at 3 PM"],
                ["Schedule a meeting with the team next week"],
                ["Help me plan my vacation to Europe"]
            ]
        }
    )
    agent_ids["assistant"] = assistant_agent["id"]
    logger.info(f"Created assistant agent: {assistant_agent['id']}")
    
    return agent_ids

async def async_main(args):
    """
    Asynchronous main function.
    
    Args:
        args: Command line arguments
    """
    try:
        # Set up configuration
        import logging
        Config.LOG_LEVEL = getattr(logging, args.log_level)
        Config.MCP_CONFIG_PATH = Path(args.mcp_config)
        
        # Use temporary directory if no registry path provided
        if args.registry_path:
            Config.REGISTRY_PATH = Path(args.registry_path)
        else:
            import tempfile
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Using temporary directory: {temp_dir}")
            Config.REGISTRY_PATH = Path(temp_dir) / "agent_registry.json"
        
        # Load MCP configuration
        Config.load_mcp_config()
        
        # Initialize components
        logger.info("Initializing Advanced AI Agency System")
        
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
        
        # Create sample agents if requested
        if args.create_sample_agents:
            agent_ids = await create_sample_agents(agent_factory)
            logger.info(f"Created sample agents: {agent_ids}")
        
        # Create API server
        logger.info("Creating API server")
        api_server = APIServer(
            registry=registry,
            agent_factory=agent_factory,
            parent_agent=parent_agent,
            mcp_manager=mcp_manager,
            a2a_server=a2a_server
        )
        
        # Print startup information
        logger.info(f"Advanced AI Agency System initialized")
        logger.info(f"API server available at http://{args.host}:{args.port}")
        logger.info(f"API endpoints:")
        logger.info(f"  - GET    /agents - List all agents")
        logger.info(f"  - POST   /agents - Create a new agent")
        logger.info(f"  - GET    /agents/:id - Get agent details")
        logger.info(f"  - PUT    /agents/:id - Update agent")
        logger.info(f"  - DELETE /agents/:id - Delete agent")
        logger.info(f"  - POST   /agents/:id/message - Send message to agent")
        logger.info(f"A2A endpoints:")
        logger.info(f"  - GET    /.well-known/agent.json - Get agency agent card")
        logger.info(f"  - GET    /agents/:id/.well-known/agent.json - Get agent card")
        logger.info(f"  - POST   /agents/:id - Handle agent request")
        logger.info(f"  - POST   /agency - Handle agency request")
        
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
