"""
MCP (Model Context Protocol) integration base classes.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = None


@dataclass
class MCPResource:
    """MCP resource definition."""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPClient(ABC):
    """Base class for MCP clients."""
    
    def __init__(self, server_url: str, auth_token: str = None):
        self.server_url = server_url
        self.auth_token = auth_token
        self._tools: List[MCPTool] = []
        self._resources: List[MCPResource] = []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize connection to MCP server."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        """List available resources."""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass
    
    async def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name."""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    async def refresh_tools(self):
        """Refresh tool list from server."""
        self._tools = await self.list_tools()
    
    async def refresh_resources(self):
        """Refresh resource list from server."""
        self._resources = await self.list_resources()


class MCPToolWrapper:
    """Wrapper to make MCP tools compatible with agent tool interface."""
    
    def __init__(self, mcp_client: MCPClient, tool: MCPTool):
        self.mcp_client = mcp_client
        self.tool = tool
    
    @property
    def name(self) -> str:
        return self.tool.name
    
    @property
    def description(self) -> str:
        return self.tool.description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return self.tool.input_schema
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        return await self.mcp_client.call_tool(self.tool.name, kwargs)