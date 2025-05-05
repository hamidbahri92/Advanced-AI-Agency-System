#!/usr/bin/env python3
"""
Basic example of an AI Agency System.

This example demonstrates how to create a simple AI Agency with a parent agent
that can create and communicate with child agents.
"""

import os
import asyncio
from pathlib import Path

from agency.config import Config
from agency.agent_registry import AgentRegistry
from agency.agent_factory import AgentFactory
from agency.parent_agent import ParentAgent
from agency.communication.mcp_integration import MCPServerManager
from agency.utils.logging import get_logger

logger = get_logger(__name__)

async def main():
    """Main function for the basic agency example."""
    try:
        # Use temporary directories for persistence
        import tempfile
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Set up paths
        registry_path = Path(temp_dir) / "agent_registry.json"
        
        # Create MCP server manager
        logger.info("Creating MCP server manager")
        mcp_manager = MCPServerManager(Config.MCP_CONFIG_PATH)
        
        # Create agent registry
        logger.info("Creating agent registry")
        registry = AgentRegistry(registry_path)
        
        # Create agent factory
        logger.info("Creating agent factory")
        agent_factory = AgentFactory(registry, mcp_manager)
        
        # Create parent agent
        logger.info("Creating parent agent")
        parent_agent = ParentAgent(registry, agent_factory, mcp_manager)
        
        # Create some agents
        logger.info("Creating agents")
        
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
        logger.info(f"Created analyst agent: {analyst_agent['id']}")
        
        # Demonstrate agent communication
        logger.info("Demonstrating agent communication")
        
        # Get a response from the writer agent
        writer_response = await parent_agent.get_agent_response(
            writer_agent["id"],
            "Write a short poem about artificial intelligence"
        )
        logger.info(f"Writer agent response: {writer_response}")
        
        # Get a response from the analyst agent
        analyst_response = await parent_agent.get_agent_response(
            analyst_agent["id"],
            "Explain how to calculate the mean and median of a dataset"
        )
        logger.info(f"Analyst agent response: {analyst_response}")
        
        # Clean up
        logger.info("Cleaning up")
        
        # Delete the agents
        agent_factory.delete_agent(writer_agent["id"])
        agent_factory.delete_agent(analyst_agent["id"])
        
        # Remove temporary directory
        import shutil
        shutil.rmtree(temp_dir)
        
        logger.info("Done")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the asynchronous main function
    asyncio.run(main())
