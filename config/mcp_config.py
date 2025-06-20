import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_web_search_mcp_params():
    """Get MCP server parameters for web search (Brave Search)"""
    if not BRAVE_API_KEY:
        raise ValueError("BRAVE_API_KEY not found in environment variables")
    
    return {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": BRAVE_API_KEY}
    }

def get_fetch_mcp_params():
    """Get MCP server parameters for web page fetching"""
    return {
        "command": "uvx", 
        "args": ["mcp-server-fetch"]
    }

def get_memory_mcp_params(session_id="default"):
    """Get MCP server parameters for memory/knowledge graph"""
    return {
        "command": "npx",
        "args": ["-y", "mcp-memory-libsql"],
        "env": {"LIBSQL_URL": f"file:./memory/{session_id}.db"}
    }

# All research MCP servers (used by research agent)
def get_research_mcp_server_params(session_id="default"):
    """Get all MCP server parameters needed for research"""
    return [
        get_web_search_mcp_params(),
        get_fetch_mcp_params(),
        get_memory_mcp_params(session_id)
    ]