# Advanced AI Agency System

A comprehensive implementation of an autonomous AI agency system that allows AI agents to create, manage, and collaborate with other AI agents to accomplish complex tasks.

## Overview

This system leverages three key technologies to create a powerful multi-agent framework:

1. **Google's Agent Development Kit (ADK)**: A flexible, modular framework for developing and deploying AI agents.
2. **Anthropic's Model Context Protocol (MCP)**: An open standard for connecting AI assistants to external systems.
3. **Google's Agent-to-Agent (A2A) Protocol**: A protocol for enabling agents to communicate and collaborate with each other.

Together, these technologies form the foundation for a system where:

- A parent agent can create and manage specialized child agents
- Agents can communicate with each other using standardized protocols
- Agents can leverage external tools and data sources through MCP
- Workflows can be created combining multiple agents with different specializations

## Features

- **Dynamic Agent Creation**: Create specialized agents with different skills, models, and capabilities
- **Agent Registry**: Keep track of all agents in the system with persistence and query capabilities
- **Parent Agent**: Central agent that can create, manage, and communicate with child agents
- **MCP Integration**: Connect to various MCP servers for tool access
- **A2A Protocol Support**: Enable standardized communication between agents
- **API Server**: RESTful API for interacting with the agency
- **Multiple Model Support**: Use different LLM models (Gemini, Claude, GPT, etc.)
- **Template-Based Agent Creation**: Create agents from predefined templates
- **Multi-Agent Workflows**: Create complex workflows with multiple agents working together

## Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher (for MCP servers)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ai-agency.git
cd ai-agency
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package and dependencies:

```bash
pip install -e .
```

4. Set up environment variables by copying the example file:

```bash
cp .env.example .env
```

5. Edit the `.env` file to add your API keys and other configuration.

## Configuration

The system is configured through the following files:

- `.env`: Environment variables for API keys, server settings, etc.
- `mcp_config.yaml`: Configuration for MCP servers

Important environment variables:

- `MODEL_API_KEY`: API key for LLM models
- `API_KEY`: API key for the agency API
- `SERVER_HOST` and `SERVER_PORT`: Host and port for the API server

## Usage

### Running the Agency

To start the AI Agency System:

```bash
python main.py
```

This will start the API server and initialize all components.

### Command Line Options

```
usage: main.py [-h] [--host HOST] [--port PORT] [--mcp-config MCP_CONFIG]
               [--registry-path REGISTRY_PATH]
               [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--debug]

AI Agency System

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host to bind to (default: 0.0.0.0)
  --port PORT           Port to listen on (default: 8000)
  --mcp-config MCP_CONFIG
                        Path to MCP configuration file (default: mcp_config.yaml)
  --registry-path REGISTRY_PATH
                        Path to agent registry file (default: data/agent_registry.json)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: INFO)
  --debug               Enable debug mode
```

### Examples

The `examples/` directory contains several example implementations:

- `basic_agency.py`: A simple AI Agency with a parent agent and a few child agents
- `multi_agent_workflow.py`: A workflow with multiple specialized agents working together
- `advanced_agency.py`: A full-featured AI Agency with API server and sample agents

To run an example:

```bash
python examples/basic_agency.py
```

### API Endpoints

The API server provides the following endpoints:

#### Authentication

- `POST /auth/token`: Get a JWT token for API access
- `POST /auth/api-key`: Generate a new API key (admin only)
- `GET /auth/me`: Get information about the currently authenticated user

#### Agents

- `GET /agents`: List all agents
- `POST /agents`: Create a new agent
- `GET /agents/{agent_id}`: Get agent details
- `PUT /agents/{agent_id}`: Update agent
- `DELETE /agents/{agent_id}`: Delete agent
- `POST /agents/{agent_id}/message`: Send message to agent
- `POST /agents/{agent_id}/activate`: Activate agent
- `POST /agents/{agent_id}/deactivate`: Deactivate agent

#### A2A Protocol

- `GET /.well-known/agent.json`: Get agency agent card
- `GET /agents/{agent_id}/.well-known/agent.json`: Get agent card
- `POST /agents/{agent_id}`: Handle agent request
- `POST /agency`: Handle agency request

## Architecture

The system is organized into the following components:

- **Parent Agent**: Central agent that manages other agents
- **Agent Registry**: Keeps track of all agents in the system
- **Agent Factory**: Creates and manages agent instances
- **MCP Integration**: Connects to MCP servers for tool access
- **A2A Client**: Communicates with other agents using the A2A protocol
- **A2A Server**: Serves agent endpoints for A2A communication
- **API Server**: Provides RESTful API for interacting with the agency

## Creating Agents

Agents can be created with different skills, models, and capabilities. For example:

```python
agent_info = agent_factory.create_agent(
    name="Creative Writer",
    description="An agent specialized in creative writing and content creation",
    skills=["creative_writing", "storytelling", "content_creation"],
    model="claude-3-opus-20240229",
    instructions="Focus on producing engaging and creative content.",
    mcp_servers=["filesystem", "fetch"],
    metadata={
        "category": "creative",
        "examples": [
            ["Write a short story about a robot discovering emotions"],
            ["Create a blog post about sustainable travel"],
            ["Draft a product description for a new smartphone"]
        ]
    }
)
```

## Communicating with Agents

Agents can communicate with each other using the A2A protocol:

```python
response = await parent_agent.get_agent_response(
    agent_id,
    "Write a short poem about artificial intelligence"
)
```

## MCP Servers

The system supports connecting to various MCP servers for tool access. The following MCP servers are included by default:

- `filesystem`: Access to the local filesystem
- `fetch`: Access to web content via HTTP requests
- `git`: Access to Git repositories
- `github`: Access to GitHub repositories
- `postgres`: Access to PostgreSQL databases
- `jira`: Access to Jira issues
- `slack`: Access to Slack messages
- `confluence`: Access to Confluence pages
- `notion`: Access to Notion pages
- `vscode`: Access to VSCode editor
- `mongodb`: Access to MongoDB databases
- `s3`: Access to AWS S3 buckets
- `redis`: Access to Redis databases

## Models

The system supports multiple LLM models:

- Gemini models (gemini-2.0-pro, gemini-2.0-flash, gemini-2.0-vision, etc.)
- Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku, etc.)
- GPT models (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
- Mistral models (mistral-large, mistral-medium, mistral-small, etc.)
- Llama models (llama-3-70b-instruct, llama-3-8b-instruct, etc.)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Google for the Agent Development Kit (ADK)
- Anthropic for the Model Context Protocol (MCP)
- Google for the Agent-to-Agent (A2A) Protocol
