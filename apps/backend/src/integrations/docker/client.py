"""
Docker integration for container operations.
"""
import docker
from typing import Any, Dict, List, Optional, BinaryIO
from pathlib import Path

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import MCPError
from apps.backend.src.integrations.mcp.base import MCPClient, MCPTool, MCPResource


class DockerClient:
    """Docker API client."""
    
    def __init__(self):
        self.client = docker.DockerClient(
            base_url=settings.DOCKER_HOST,
            timeout=60,
        )
    
    def build_image(
        self,
        path: str,
        tag: str,
        dockerfile: str = "Dockerfile",
        build_args: Dict[str, str] = None,
    ) -> Any:
        """Build Docker image."""
        image, logs = self.client.images.build(
            path=path,
            tag=tag,
            dockerfile=dockerfile,
            buildargs=build_args,
            rm=True,
        )
        return image
    
    def push_image(self, tag: str, auth_config: Dict[str, str] = None) -> List[Dict]:
        """Push Docker image to registry."""
        return self.client.images.push(tag, auth_config=auth_config, stream=True, decode=True)
    
    def run_container(
        self,
        image: str,
        command: str = None,
        environment: Dict[str, str] = None,
        ports: Dict[str, int] = None,
        volumes: Dict[str, Dict] = None,
        detach: bool = True,
        name: str = None,
    ) -> Any:
        """Run a container."""
        return self.client.containers.run(
            image=image,
            command=command,
            environment=environment,
            ports=ports,
            volumes=volumes,
            detach=detach,
            name=name,
        )
    
    def get_container(self, container_id: str) -> Any:
        """Get container by ID."""
        return self.client.containers.get(container_id)
    
    def list_containers(self, all: bool = True) -> List[Any]:
        """List containers."""
        return self.client.containers.list(all=all)
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
        container = self.get_container(container_id)
        container.stop(timeout=timeout)
        return True
    
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a container."""
        container = self.get_container(container_id)
        container.remove(force=force)
        return True
    
    def get_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs."""
        container = self.get_container(container_id)
        return container.logs(tail=tail).decode("utf-8")
    
    def exec_command(self, container_id: str, command: str) -> tuple:
        """Execute command in container."""
        container = self.get_container(container_id)
        return container.exec_run(command)
    
    def create_network(self, name: str, driver: str = "bridge") -> Any:
        """Create Docker network."""
        return self.client.networks.create(name=name, driver=driver)
    
    def create_volume(self, name: str = None) -> Any:
        """Create Docker volume."""
        return self.client.volumes.create(name=name)


class DockerMCPClient(MCPClient):
    """MCP client for Docker operations."""
    
    def __init__(self):
        super().__init__("docker://local")
        self.docker_client = DockerClient()
    
    async def initialize(self) -> bool:
        """Initialize Docker connection."""
        try:
            self.docker_client.client.ping()
            return True
        except Exception:
            return False
    
    async def list_tools(self) -> List[MCPTool]:
        """List available Docker tools."""
        self._tools = [
            MCPTool(
                name="build_image",
                description="Build a Docker image",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "tag": {"type": "string"},
                        "dockerfile": {"type": "string"},
                        "build_args": {"type": "object"},
                    },
                    "required": ["path", "tag"],
                },
            ),
            MCPTool(
                name="push_image",
                description="Push Docker image to registry",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tag": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "registry": {"type": "string"},
                    },
                    "required": ["tag"],
                },
            ),
            MCPTool(
                name="run_container",
                description="Run a Docker container",
                input_schema={
                    "type": "object",
                    "properties": {
                        "image": {"type": "string"},
                        "command": {"type": "string"},
                        "environment": {"type": "object"},
                        "ports": {"type": "object"},
                        "volumes": {"type": "object"},
                        "name": {"type": "string"},
                    },
                    "required": ["image"],
                },
            ),
            MCPTool(
                name="stop_container",
                description="Stop a Docker container",
                input_schema={
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string"},
                        "timeout": {"type": "integer"},
                    },
                    "required": ["container_id"],
                },
            ),
            MCPTool(
                name="get_logs",
                description="Get container logs",
                input_schema={
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string"},
                        "tail": {"type": "integer"},
                    },
                    "required": ["container_id"],
                },
            ),
            MCPTool(
                name="list_containers",
                description="List Docker containers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "all": {"type": "boolean"},
                    },
                },
            ),
        ]
        return self._tools
    
    async def list_resources(self) -> List[MCPResource]:
        """List available Docker resources."""
        self._resources = [
            MCPResource(
                uri="docker://images",
                name="Docker Images",
                description="List of local Docker images",
            ),
            MCPResource(
                uri="docker://containers",
                name="Docker Containers",
                description="List of Docker containers",
            ),
            MCPResource(
                uri="docker://networks",
                name="Docker Networks",
                description="List of Docker networks",
            ),
            MCPResource(
                uri="docker://volumes",
                name="Docker Volumes",
                description="List of Docker volumes",
            ),
        ]
        return self._resources
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a Docker tool."""
        if name == "build_image":
            image = self.docker_client.build_image(
                path=arguments["path"],
                tag=arguments["tag"],
                dockerfile=arguments.get("dockerfile", "Dockerfile"),
                build_args=arguments.get("build_args"),
            )
            return {"id": image.id, "tags": image.tags}
        
        elif name == "push_image":
            auth_config = None
            if arguments.get("username") and arguments.get("password"):
                auth_config = {
                    "username": arguments["username"],
                    "password": arguments["password"],
                    "registry": arguments.get("registry", "https://index.docker.io/v1/"),
                }
            result = self.docker_client.push_image(arguments["tag"], auth_config)
            return list(result)
        
        elif name == "run_container":
            container = self.docker_client.run_container(
                image=arguments["image"],
                command=arguments.get("command"),
                environment=arguments.get("environment"),
                ports=arguments.get("ports"),
                volumes=arguments.get("volumes"),
                name=arguments.get("name"),
            )
            return {"id": container.id, "name": container.name}
        
        elif name == "stop_container":
            self.docker_client.stop_container(
                container_id=arguments["container_id"],
                timeout=arguments.get("timeout", 10),
            )
            return {"success": True}
        
        elif name == "get_logs":
            logs = self.docker_client.get_logs(
                container_id=arguments["container_id"],
                tail=arguments.get("tail", 100),
            )
            return {"logs": logs}
        
        elif name == "list_containers":
            containers = self.docker_client.list_containers(arguments.get("all", True))
            return [
                {
                    "id": c.id[:12],
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "status": c.status,
                    "ports": c.ports,
                }
                for c in containers
            ]
        
        raise MCPError("docker", f"Unknown tool: {name}")
    
    async def read_resource(self, uri: str) -> Any:
        """Read a Docker resource."""
        if uri == "docker://images":
            images = self.docker_client.client.images.list()
            return [
                {
                    "id": img.id[:12],
                    "tags": img.tags,
                    "size": img.attrs.get("Size", 0),
                }
                for img in images
            ]
        
        elif uri == "docker://containers":
            containers = self.docker_client.list_containers()
            return [
                {
                    "id": c.id[:12],
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "status": c.status,
                }
                for c in containers
            ]
        
        elif uri == "docker://networks":
            networks = self.docker_client.client.networks.list()
            return [
                {"id": n.id[:12], "name": n.name, "driver": n.attrs.get("Driver")}
                for n in networks
            ]
        
        elif uri == "docker://volumes":
            volumes = self.docker_client.client.volumes.list()
            return [
                {"name": v.name, "driver": v.attrs.get("Driver"), "mountpoint": v.attrs.get("Mountpoint")}
                for v in volumes
            ]
        
        raise MCPError("docker", f"Unknown resource: {uri}")
    
    async def close(self):
        """Close Docker client."""
        self.docker_client.client.close()


# Global instance
_docker_client: Optional[DockerClient] = None
_docker_mcp_client: Optional[DockerMCPClient] = None


def get_docker_client() -> DockerClient:
    """Get or create Docker client."""
    global _docker_client
    if _docker_client is None:
        _docker_client = DockerClient()
    return _docker_client


def get_docker_mcp_client() -> DockerMCPClient:
    """Get or create Docker MCP client."""
    global _docker_mcp_client
    if _docker_mcp_client is None:
        _docker_mcp_client = DockerMCPClient()
    return _docker_mcp_client