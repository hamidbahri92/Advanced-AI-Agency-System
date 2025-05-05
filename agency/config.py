import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration for the AI Agency System."""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Registry path
    REGISTRY_PATH = DATA_DIR / "agent_registry.json"
    
    # Agent Cards directory for A2A
    AGENT_CARDS_DIR = DATA_DIR / "agent_cards"
    AGENT_CARDS_DIR.mkdir(exist_ok=True)
    
    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # Model configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-pro")
    MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
    USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "FALSE").upper() == "TRUE"
    
    # Google Cloud configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
    GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
    
    # MCP configuration
    MCP_ENABLED = os.getenv("MCP_ENABLED", "TRUE").upper() == "TRUE"
    MCP_CONFIG_PATH = BASE_DIR / "mcp_config.yaml"
    
    # API configuration
    API_KEY = os.getenv("API_KEY", "")
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = 86400  # 24 hours
    
    # Logging configuration
    LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
    LOG_DIR.mkdir(exist_ok=True)
    
    # Security configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    ENABLE_SSL = os.getenv("ENABLE_SSL", "FALSE").upper() == "TRUE"
    SSL_CERT_FILE = os.getenv("SSL_CERT_FILE", "")
    SSL_KEY_FILE = os.getenv("SSL_KEY_FILE", "")
    
    # A2A configuration
    A2A_ENABLED = True  # A2A is always enabled
    A2A_ENDPOINT = f"http://{SERVER_HOST}:{SERVER_PORT}/a2a"
    
    # MCP servers
    MCP_SERVERS = {}
    
    @classmethod
    def load_mcp_config(cls):
        """Load MCP server configurations from YAML file."""
        if cls.MCP_CONFIG_PATH.exists():
            try:
                with open(cls.MCP_CONFIG_PATH, 'r') as f:
                    cls.MCP_SERVERS = yaml.safe_load(f)
                    
                # Replace environment variables in the configuration
                cls._replace_env_vars_in_config()
            except Exception as e:
                print(f"Error loading MCP config: {e}")
                cls.MCP_SERVERS = {}
    
    @classmethod
    def _replace_env_vars_in_config(cls):
        """Replace environment variables in the MCP configuration."""
        for server_name, server_config in cls.MCP_SERVERS.items():
            if "env" in server_config:
                for env_var, value in server_config["env"].items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_name = value[2:-1]
                        server_config["env"][env_var] = os.getenv(env_name, "")
            
            if "args" in server_config:
                for i, arg in enumerate(server_config["args"]):
                    if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                        env_name = arg[2:-1]
                        server_config["args"][i] = os.getenv(env_name, "")
    
    @classmethod
    def get_mcp_server_config(cls, server_name):
        """Get configuration for a specific MCP server."""
        return cls.MCP_SERVERS.get(server_name, {})
    
    @classmethod
    def get_available_mcp_servers(cls):
        """Get a list of all available MCP servers."""
        return list(cls.MCP_SERVERS.keys())


# Load MCP configuration
Config.load_mcp_config()
