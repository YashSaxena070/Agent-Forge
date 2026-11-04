"""
Tool execution layer with MCP integration.
"""
import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import MCPError
from apps.backend.src.integrations.mcp.base import MCPClient, MCPTool, MCPResource, MCPToolWrapper
from apps.backend.src.integrations.github.client import get_github_mcp_client
from apps.backend.src.integrations.docker.client import get_docker_mcp_client
from apps.backend.src.integrations.kubernetes.client import get_kubernetes_mcp_client


class ToolExecutor:
    """Executes tools with timeout, retries, and error handling."""
    
    def __init__(self, default_timeout: int = 300, max_retries: int = 3):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._mcp_clients: Dict[str, MCPClient] = {}
    
    async def initialize(self):
        """Initialize MCP clients."""
        if settings.ENABLE_MCP:
            # Initialize GitHub MCP
            if settings.MCP_GITHUB_ENABLED:
                try:
                    github_client = get_github_mcp_client()
                    await github_client.initialize()
                    self._mcp_clients["github"] = github_client
                except Exception as e:
                    print(f"Failed to initialize GitHub MCP: {e}")
            
            # Initialize Docker MCP
            if settings.MCP_DOCKER_ENABLED:
                try:
                    docker_client = get_docker_mcp_client()
                    await docker_client.initialize()
                    self._mcp_clients["docker"] = docker_client
                except Exception as e:
                    print(f"Failed to initialize Docker MCP: {e}")
            
            # Initialize Kubernetes MCP
            if settings.MCP_KUBERNETES_ENABLED:
                try:
                    k8s_client = get_kubernetes_mcp_client()
                    await k8s_client.initialize()
                    self._mcp_clients["kubernetes"] = k8s_client
                except Exception as e:
                    print(f"Failed to initialize Kubernetes MCP: {e}")
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
    ) -> Any:
        """Execute a tool with timeout and retries."""
        timeout = timeout or self.default_timeout
        retries = retries or self.max_retries
        
        # Find which MCP client has this tool
        for client_name, client in self._mcp_clients.items():
            tool = await client.get_tool(tool_name)
            if tool:
                return await self._execute_with_retry(
                    client_name, client, tool_name, arguments, timeout, retries
                )
        
        # Check local tools
        local_tool = LocalToolRegistry.get_tool(tool_name)
        if local_tool:
            return await self._execute_local_tool(local_tool, arguments, timeout, retries)
        
        raise MCPError("unknown", f"Tool not found: {tool_name}")
    
    async def _execute_with_retry(
        self,
        client_name: str,
        client: MCPClient,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: int,
        retries: int,
    ) -> Any:
        """Execute MCP tool with retry logic."""
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                return await asyncio.wait_for(
                    client.call_tool(tool_name, arguments),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                last_error = f"Tool {tool_name} timed out after {timeout}s"
            except Exception as e:
                last_error = str(e)
            
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise MCPError(client_name, last_error or "Unknown error", tool=tool_name)
    
    async def _execute_local_tool(
        self,
        tool: "LocalTool",
        arguments: Dict[str, Any],
        timeout: int,
        retries: int,
    ) -> Any:
        """Execute local tool with retry logic."""
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                return await asyncio.wait_for(
                    tool.execute(**arguments),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                last_error = f"Tool {tool.name} timed out after {timeout}s"
            except Exception as e:
                last_error = str(e)
            
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
        
        raise MCPError("local", last_error or "Unknown error", tool=tool.name)
    
    def get_available_tools(self) -> List[MCPTool]:
        """Get all available tools from all sources."""
        tools = []
        
        # MCP tools
        for client in self._mcp_clients.values():
            try:
                tools.extend(asyncio.run(client.list_tools()))
            except Exception:
                pass
        
        # Local tools
        for tool in LocalToolRegistry.get_all_tools():
            tools.append(MCPTool(
                name=tool.name,
                description=tool.description,
                input_schema=tool.parameters,
            ))
        
        return tools
    
    async def close(self):
        """Close all MCP clients."""
        for client in self._mcp_clients.values():
            await client.close()


class LocalTool(ABC):
    """Base class for local (in-process) tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass


class LocalToolRegistry:
    """Registry for local tools."""
    
    _tools: Dict[str, LocalTool] = {}
    
    @classmethod
    def register(cls, tool: LocalTool):
        cls._tools[tool.name] = tool
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[LocalTool]:
        return cls._tools.get(name)
    
    @classmethod
    def get_all_tools(cls) -> List[LocalTool]:
        return list(cls._tools.values())


# Example local tools
class CodeExecutionTool(LocalTool):
    """Execute code in sandbox (placeholder - would use gVisor/Firecracker)."""
    
    name = "execute_code"
    description = "Execute code in isolated sandbox"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "language": {"type": "string", "enum": ["python", "javascript", "bash"]},
            "timeout": {"type": "integer", "default": 30},
        },
        "required": ["code", "language"],
    }
    
    async def execute(self, code: str, language: str, timeout: int = 30) -> Dict[str, Any]:
        # In production, this would use a secure sandbox
        # For now, return mock result
        return {
            "stdout": "Code executed successfully",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 100,
        }


class FileSystemTool(LocalTool):
    """Local file system operations."""
    
    name = "filesystem"
    description = "Read/write files in workspace"
    parameters = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "list", "delete"]},
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["operation", "path"],
    }
    
    async def execute(self, operation: str, path: str, content: str = None) -> Any:
        import aiofiles
        import os
        
        workspace = "/workspace"
        full_path = os.path.join(workspace, path.lstrip("/"))
        
        if operation == "read":
            async with aiofiles.open(full_path, "r") as f:
                return await f.read()
        elif operation == "write":
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            async with aiofiles.open(full_path, "w") as f:
                await f.write(content or "")
            return {"success": True, "path": path}
        elif operation == "list":
            return os.listdir(full_path)
        elif operation == "delete":
            os.remove(full_path)
            return {"success": True}
        
        raise ValueError(f"Unknown operation: {operation}")


# Register local tools
LocalToolRegistry.register(CodeExecutionTool())
LocalToolRegistry.register(FileSystemTool())


# Global executor instance
_tool_executor: Optional[ToolExecutor] = None


async def get_tool_executor() -> ToolExecutor:
    """Get or create tool executor."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
        await _tool_executor.initialize()
    return _tool_executor