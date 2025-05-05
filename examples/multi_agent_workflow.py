#!/usr/bin/env python3
"""
Multi-agent workflow example for the AI Agency System.

This example demonstrates how to create a workflow with multiple specialized
agents working together to complete a complex task.
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
    """Main function for the multi-agent workflow example."""
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
        
        # Create specialized agents for the workflow
        logger.info("Creating specialized agents")
        
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
        logger.info(f"Created researcher agent: {researcher_agent['id']}")
        
        # Writer agent
        writer_agent = agent_factory.create_agent(
            name="Content Writer",
            description="An agent specialized in creating high-quality written content",
            skills=["content_creation", "storytelling", "editing"],
            model="claude-3-opus-20240229",
            metadata={
                "category": "creative",
                "examples": [
                    ["Write a blog post about remote work trends"],
                    ["Create an engaging product description for this smartphone"],
                    ["Draft an email announcing our new product launch"]
                ]
            }
        )
        logger.info(f"Created writer agent: {writer_agent['id']}")
        
        # Editor agent
        editor_agent = agent_factory.create_agent(
            name="Content Editor",
            description="An agent specialized in editing and improving written content",
            skills=["editing", "proofreading", "feedback"],
            model="claude-3-sonnet-20240229",
            metadata={
                "category": "creative",
                "examples": [
                    ["Edit this blog post for clarity and conciseness"],
                    ["Proofread this document and fix any errors"],
                    ["Provide feedback on how to improve this article"]
                ]
            }
        )
        logger.info(f"Created editor agent: {editor_agent['id']}")
        
        # Execute multi-agent workflow
        logger.info("Executing multi-agent workflow")
        
        # Step 1: Research
        research_topic = "The impact of artificial intelligence on healthcare"
        logger.info(f"Researching: {research_topic}")
        
        research_results = await parent_agent.get_agent_response(
            researcher_agent["id"],
            f"Research {research_topic} and provide key findings and statistics"
        )
        logger.info("Research completed")
        
        # Step 2: Content creation
        logger.info("Creating content based on research")
        
        writing_prompt = f"""
        Write a blog post about {research_topic} based on the following research:
        
        {research_results}
        
        The blog post should be informative, engaging, and around 500 words.
        """
        
        draft_content = await parent_agent.get_agent_response(
            writer_agent["id"],
            writing_prompt
        )
        logger.info("Content draft completed")
        
        # Step 3: Editing and refinement
        logger.info("Editing and refining content")
        
        editing_prompt = f"""
        Edit and improve the following blog post about {research_topic}:
        
        {draft_content}
        
        Focus on improving clarity, flow, and making the content more engaging.
        """
        
        final_content = await parent_agent.get_agent_response(
            editor_agent["id"],
            editing_prompt
        )
        logger.info("Editing completed")
        
        # Output the final result
        logger.info("Workflow completed. Final content:")
        print("\n" + "="*80 + "\n")
        print(f"# {research_topic.title()}\n")
        print(final_content)
        print("\n" + "="*80 + "\n")
        
        # Clean up
        logger.info("Cleaning up")
        
        # Delete the agents
        agent_factory.delete_agent(researcher_agent["id"])
        agent_factory.delete_agent(writer_agent["id"])
        agent_factory.delete_agent(editor_agent["id"])
        
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
