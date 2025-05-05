from typing import Dict, Any, Optional, List
import os
import json
from pathlib import Path

from google.adk.tools.mcp import MCPToolset

from ..utils.logging import get_logger
from ..config import Config

logger = get_logger(__name__)

def create_mcp_toolset(server_name: str, server_config: Dict[str, Any]) -> MCPToolset:
    """
    Create an MCP toolset for the specified server.
    
    Args:
        server_name: Name of the MCP server
        server_config: Configuration for the server
    
    Returns:
        MCPToolset instance
    
    Raises:
        ValueError: If the server type is not supported
    """
    server_type = server_config.get("type", "stdio")
    
    if server_type == "stdio":
        # Create a stdio MCP server
        return MCPToolset(
            parameters={
                "server_type": "stdio",
                "command": server_config.get("command"),
                "args": server_config.get("args", []),
                "cwd": server_config.get("cwd"),
                "env": server_config.get("env", {}),
                "cache_tools_list": server_config.get("cache_tools_list", False)
            }
        )
    elif server_type == "sse":
        # Create an SSE MCP server
        return MCPToolset(
            parameters={
                "server_type": "sse",
                "url": server_config.get("url"),
                "headers": server_config.get("headers", {}),
                "cache_tools_list": server_config.get("cache_tools_list", False)
            }
        )
    elif server_type == "websocket":
        # Create a WebSocket MCP server
        return MCPToolset(
            parameters={
                "server_type": "websocket",
                "url": server_config.get("url"),
                "headers": server_config.get("headers", {}),
                "cache_tools_list": server_config.get("cache_tools_list", False)
            }
        )
    elif server_type == "http":
        # Create an HTTP MCP server
        return MCPToolset(
            parameters={
                "server_type": "http",
                "url": server_config.get("url"),
                "headers": server_config.get("headers", {}),
                "cache_tools_list": server_config.get("cache_tools_list", False)
            }
        )
    else:
        raise ValueError(f"Unsupported MCP server type: {server_type}")

def load_mcp_servers(config_path: Optional[Path] = None) -> List[MCPToolset]:
    """
    Load all configured MCP servers.
    
    Args:
        config_path: Optional path to the MCP configuration file
    
    Returns:
        List of MCPToolset instances
    """
    # Make sure the configuration is loaded
    if config_path:
        Config.load_mcp_config()
    
    mcp_servers = []
    
    # Skip if MCP is disabled
    if not Config.MCP_ENABLED:
        logger.info("MCP is disabled, skipping server loading")
        return mcp_servers
    
    for server_name, server_config in Config.MCP_SERVERS.items():
        try:
            mcp_toolset = create_mcp_toolset(server_name, server_config)
            mcp_servers.append(mcp_toolset)
            logger.info(f"Loaded MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to load MCP server {server_name}: {e}")
    
    return mcp_servers

class MCPServerManager:
    """
    Manager for MCP servers, providing methods for loading, reloading, and accessing MCP toolsets.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the MCP server manager.
        
        Args:
            config_path: Optional path to the MCP configuration file
        """
        self.config_path = config_path or Config.MCP_CONFIG_PATH
        self.mcp_servers: Dict[str, MCPToolset] = {}
        self.load_servers()
    
    def load_servers(self):
        """Load all configured MCP servers."""
        # Skip if MCP is disabled
        if not Config.MCP_ENABLED:
            logger.info("MCP is disabled, skipping server loading")
            return
        
        # Make sure the configuration is loaded
        Config.load_mcp_config()
        
        for server_name, server_config in Config.MCP_SERVERS.items():
            try:
                mcp_toolset = create_mcp_toolset(server_name, server_config)
                self.mcp_servers[server_name] = mcp_toolset
                logger.info(f"Loaded MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Failed to load MCP server {server_name}: {e}")
    
    def reload_servers(self):
        """Reload all MCP servers."""
        # Close any open servers
        for server_name, toolset in self.mcp_servers.items():
            try:
                # Close the server if it has a close method
                if hasattr(toolset, 'close'):
                    toolset.close()
            except Exception as e:
                logger.error(f"Failed to close MCP server {server_name}: {e}")
        
        # Clear the servers
        self.mcp_servers.clear()
        
        # Reload the configuration
        Config.load_mcp_config()
        
        # Load the servers again
        self.load_servers()
    
    def get_server(self, server_name: str) -> Optional[MCPToolset]:
        """
        Get an MCP server by name.
        
        Args:
            server_name: Name of the MCP server
        
        Returns:
            MCPToolset instance or None if not found
        """
        return self.mcp_servers.get(server_name)
    
    def get_all_servers(self) -> List[MCPToolset]:
        """
        Get all MCP servers.
        
        Returns:
            List of MCPToolset instances
        """
        return list(self.mcp_servers.values())
    
    def get_servers_by_type(self, server_type: str) -> List[MCPToolset]:
        """
        Get all MCP servers of a specific type.
        
        Args:
            server_type: Type of MCP server (e.g., 'stdio', 'sse')
        
        Returns:
            List of MCPToolset instances
        """
        return [
            toolset for server_name, toolset in self.mcp_servers.items()
            if Config.MCP_SERVERS.get(server_name, {}).get("type") == server_type
        ]
    
    def close(self):
        """Close all MCP servers."""
        for server_name, toolset in self.mcp_servers.items():
            try:
                # Close the server if it has a close method
                if hasattr(toolset, 'close'):
                    toolset.close()
            except Exception as e:
                logger.error(f"Failed to close MCP server {server_name}: {e}")
        
        # Clear the servers
        self.mcp_servers.clear()
    
    def get_tools_for_server(self, server_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of all tools available for a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
        
        Returns:
            List of tool information dictionaries
        """
        server = self.get_server(server_name)
        if not server:
            return []
        
        try:
            # Call the list_tools method if available
            if hasattr(server, 'list_tools'):
                return server.list_tools()
            
            return []
        except Exception as e:
            logger.error(f"Failed to list tools for MCP server {server_name}: {e}")
            return []
    
    def get_all_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get a dictionary of all available tools for all MCP servers.
        
        Returns:
            Dictionary mapping server names to lists of tool information dictionaries
        """
        tools = {}
        
        for server_name in self.mcp_servers:
            server_tools = self.get_tools_for_server(server_name)
            if server_tools:
                tools[server_name] = server_tools
        
        return tools
    
    def execute_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a tool on a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            params: Parameters for the tool
        
        Returns:
            Result of the tool execution
        
        Raises:
            ValueError: If the server or tool is not found
        """
        server = self.get_server(server_name)
        if not server:
            raise ValueError(f"MCP server not found: {server_name}")
        
        try:
            # Call the execute_tool method
            return server.execute_tool(tool_name, params)
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name} on MCP server {server_name}: {e}")
            raise
