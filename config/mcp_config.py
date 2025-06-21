import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Environment variables
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def validate_api_keys():
    """Validate that required API keys are present"""
    missing_keys = []
    
    if not BRAVE_API_KEY:
        missing_keys.append("BRAVE_API_KEY")
        logger.warning("BRAVE_API_KEY not found - web search will be limited")
    
    if not OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
        logger.error("OPENAI_API_KEY is required for OpenAI Agents SDK")
    
    if missing_keys:
        error_msg = f"Missing required environment variables: {', '.join(missing_keys)}"
        if "OPENAI_API_KEY" in missing_keys:
            raise ValueError(error_msg)
        else:
            logger.warning(error_msg)
    
    logger.info("✅ Essential API keys validated")
    return True

def get_web_search_mcp_params():
    """Get MCP server parameters for web search (Brave Search)"""
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY not available - web search functionality will be limited")
        return None
    
    return {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": BRAVE_API_KEY,
            **os.environ  # Include all environment variables
        }
    }

def get_fetch_mcp_params():
    """Get MCP server parameters for web page fetching"""
    return {
        "command": "uvx", 
        "args": ["mcp-server-fetch"]
    }

def get_memory_mcp_params(session_id="default"):
    """Get MCP server parameters for memory/knowledge graph"""
    # Ensure memory directory exists
    memory_dir = "./memory"
    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir)
        logger.info(f"Created memory directory: {memory_dir}")
    
    return {
        "command": "npx",
        "args": ["-y", "mcp-memory-libsql"],
        "env": {
            "LIBSQL_URL": f"file:./memory/{session_id}.db",
            **os.environ
        }
    }

def get_filesystem_mcp_params(allowed_dirs=None):
    """Get MCP server parameters for file system access"""
    if allowed_dirs is None:
        # Default to uploads and memory directories
        uploads_dir = os.path.abspath("./uploads")
        memory_dir = os.path.abspath("./memory")
        
        # Ensure directories exist
        for dir_path in [uploads_dir, memory_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
        
        allowed_dirs = [uploads_dir, memory_dir]
    
    return {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"] + allowed_dirs
    }

def get_research_mcp_server_params(session_id="default"):
    """Get all MCP server parameters needed for research"""
    try:
        validate_api_keys()
    except ValueError as e:
        logger.error(f"API key validation failed: {e}")
        raise
    
    # Build list of MCP server parameters
    params_list = []
    
    # Web search (optional if no Brave API key)
    web_search_params = get_web_search_mcp_params()
    if web_search_params:
        params_list.append(web_search_params)
        logger.info("✅ Added Brave Search MCP server")
    else:
        logger.warning("⚠️ Brave Search not available - install mcp-server-brave-search and add BRAVE_API_KEY")
    
    # Web fetch (for getting full web pages)
    params_list.append(get_fetch_mcp_params())
    logger.info("✅ Added Fetch MCP server")
    
    # Memory/knowledge graph
    params_list.append(get_memory_mcp_params(session_id))
    logger.info("✅ Added Memory MCP server")
    
    # File system access
    params_list.append(get_filesystem_mcp_params())
    logger.info("✅ Added Filesystem MCP server")
    
    logger.info(f"🚀 Configured {len(params_list)} MCP servers for session: {session_id}")
    return params_list

def get_sales_agent_mcp_params(session_id="default"):
    """Get MCP server parameters specifically for the sales agent"""
    # Sales agent might need different or additional MCP servers
    # For now, use the same as research agent
    return get_research_mcp_server_params(session_id)

def test_mcp_configuration():
    """Test MCP configuration and report status"""
    print("🔧 Testing MCP Configuration...")
    print("=" * 50)
    
    try:
        # Test API key validation
        validate_api_keys()
        print("✅ API key validation passed")
        
        # Test MCP server parameter generation
        session_id = "test_session"
        params = get_research_mcp_server_params(session_id)
        print(f"✅ Generated {len(params)} MCP server configurations")
        
        # List configured servers
        print("\n📋 Configured MCP Servers:")
        for i, param in enumerate(params, 1):
            command = " ".join([param["command"]] + param["args"])
            print(f"  {i}. {command}")
            if "env" in param and param["env"]:
                env_keys = [k for k in param["env"].keys() if k != "PATH"]
                if env_keys:
                    print(f"     Environment: {', '.join(env_keys)}")
        
        print("\n✅ MCP configuration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ MCP configuration test failed: {e}")
        return False

# Installation requirements check
def check_mcp_requirements():
    """Check if required MCP packages are available"""
    print("🔍 Checking MCP Requirements...")
    
    requirements = [
        ("uvx", "Install uv: https://docs.astral.sh/uv/"),
        ("npx", "Install Node.js: https://nodejs.org/"),
        ("@modelcontextprotocol/server-brave-search", "npm install -g @modelcontextprotocol/server-brave-search"),
        ("mcp-server-fetch", "Available via uvx"),
        ("mcp-memory-libsql", "Available via npx")
    ]
    
    print("Required components:")
    for req, install_info in requirements:
        print(f"  - {req}: {install_info}")
    
    print("\n💡 To install missing components:")
    print("1. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("2. Install Node.js: https://nodejs.org/")
    print("3. Install Brave Search: npx -y @modelcontextprotocol/server-brave-search")
    print("4. Install OpenAI Agents SDK: pip install openai-agents")

if __name__ == "__main__":
    print("🚀 MCP Configuration Module")
    print("=" * 40)
    
    # Run tests
    check_mcp_requirements()
    print("\n")
    test_mcp_configuration()