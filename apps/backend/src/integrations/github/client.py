"""
GitHub integration for MCP and direct API access.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from github import Github, GithubIntegration
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Issue import Issue

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import MCPError
from apps.backend.src.integrations.mcp.base import MCPClient, MCPTool, MCPResource


class GitHubClient:
    """GitHub API client."""
    
    def __init__(self, token: str = None):
        self.token = token or settings.GITHUB_TOKEN
        if not self.token:
            raise MCPError("github", "GitHub token not configured")
        self.client = Github(self.token)
    
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository by owner and name."""
        return self.client.get_repo(f"{owner}/{repo}")
    
    async def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
    ) -> Repository:
        """Create a new repository."""
        user = self.client.get_user()
        return user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=auto_init,
        )
    
    async def create_pull_request(
        self,
        repo: Repository,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> PullRequest:
        """Create a pull request."""
        return repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base,
        )
    
    async def create_issue(
        self,
        repo: Repository,
        title: str,
        body: str = "",
        labels: List[str] = None,
    ) -> Issue:
        """Create an issue."""
        return repo.create_issue(
            title=title,
            body=body,
            labels=labels or [],
        )
    
    async def get_file_content(self, repo: Repository, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        try:
            content = repo.get_contents(path, ref=ref)
            return content.decoded_content.decode("utf-8")
        except Exception:
            return ""
    
    async def create_file(
        self,
        repo: Repository,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Create or update a file."""
        try:
            # Try to get existing file
            existing = repo.get_contents(path, ref=branch)
            result = repo.update_file(
                path=path,
                message=message,
                content=content,
                sha=existing.sha,
                branch=branch,
            )
        except Exception:
            result = repo.create_file(
                path=path,
                message=message,
                content=content,
                branch=branch,
            )
        return result
    
    async def create_branch(self, repo: Repository, branch_name: str, from_branch: str = "main") -> Any:
        """Create a new branch."""
        source = repo.get_branch(from_branch)
        return repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)


class GitHubMCPClient(MCPClient):
    """MCP client for GitHub server."""
    
    def __init__(self, server_url: str = "http://localhost:3000", auth_token: str = None):
        super().__init__(server_url, auth_token)
        self.github_client = GitHubClient(auth_token)
    
    async def initialize(self) -> bool:
        """Initialize connection."""
        try:
            # Test GitHub connection
            user = self.github_client.client.get_user()
            return user is not None
        except Exception:
            return False
    
    async def list_tools(self) -> List[MCPTool]:
        """List available GitHub tools."""
        self._tools = [
            MCPTool(
                name="create_repository",
                description="Create a new GitHub repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "private": {"type": "boolean"},
                    },
                    "required": ["name"],
                },
            ),
            MCPTool(
                name="create_pull_request",
                description="Create a pull request",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "head": {"type": "string"},
                        "base": {"type": "string"},
                    },
                    "required": ["owner", "repo", "title", "head"],
                },
            ),
            MCPTool(
                name="create_issue",
                description="Create an issue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["owner", "repo", "title"],
                },
            ),
            MCPTool(
                name="get_file",
                description="Get file content from repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "path": {"type": "string"},
                        "ref": {"type": "string"},
                    },
                    "required": ["owner", "repo", "path"],
                },
            ),
            MCPTool(
                name="create_file",
                description="Create or update a file in repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "message": {"type": "string"},
                        "branch": {"type": "string"},
                    },
                    "required": ["owner", "repo", "path", "content", "message"],
                },
            ),
            MCPTool(
                name="create_branch",
                description="Create a new branch",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "branch_name": {"type": "string"},
                        "from_branch": {"type": "string"},
                    },
                    "required": ["owner", "repo", "branch_name"],
                },
            ),
        ]
        return self._tools
    
    async def list_resources(self) -> List[MCPResource]:
        """List available GitHub resources."""
        self._resources = [
            MCPResource(
                uri="github://repositories",
                name="Repositories",
                description="List of accessible repositories",
            ),
            MCPResource(
                uri="github://user",
                name="Current User",
                description="Authenticated user information",
            ),
        ]
        return self._resources
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a GitHub tool."""
        owner = arguments.get("owner")
        repo_name = arguments.get("repo")
        
        if owner and repo_name:
            repo = await self.github_client.get_repository(owner, repo_name)
        else:
            repo = None
        
        if name == "create_repository":
            return await self.github_client.create_repository(
                name=arguments["name"],
                description=arguments.get("description", ""),
                private=arguments.get("private", True),
            )
        
        elif name == "create_pull_request":
            return await self.github_client.create_pull_request(
                repo=repo,
                title=arguments["title"],
                body=arguments.get("body", ""),
                head=arguments["head"],
                base=arguments.get("base", "main"),
            )
        
        elif name == "create_issue":
            return await self.github_client.create_issue(
                repo=repo,
                title=arguments["title"],
                body=arguments.get("body", ""),
                labels=arguments.get("labels", []),
            )
        
        elif name == "get_file":
            return await self.github_client.get_file_content(
                repo=repo,
                path=arguments["path"],
                ref=arguments.get("ref", "main"),
            )
        
        elif name == "create_file":
            return await self.github_client.create_file(
                repo=repo,
                path=arguments["path"],
                content=arguments["content"],
                message=arguments["message"],
                branch=arguments.get("branch", "main"),
            )
        
        elif name == "create_branch":
            return await self.github_client.create_branch(
                repo=repo,
                branch_name=arguments["branch_name"],
                from_branch=arguments.get("from_branch", "main"),
            )
        
        raise MCPError("github", f"Unknown tool: {name}")
    
    async def read_resource(self, uri: str) -> Any:
        """Read a GitHub resource."""
        if uri == "github://user":
            user = self.github_client.client.get_user()
            return {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "public_repos": user.public_repos,
            }
        elif uri == "github://repositories":
            repos = self.github_client.client.get_user().get_repos()
            return [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "private": r.private,
                    "description": r.description,
                }
                for r in repos[:50]
            ]
        
        raise MCPError("github", f"Unknown resource: {uri}")
    
    async def close(self):
        """Close the connection."""
        self.github_client.client.close()


# Global instance
_github_client: Optional[GitHubClient] = None
_github_mcp_client: Optional[GitHubMCPClient] = None


def get_github_client() -> GitHubClient:
    """Get or create GitHub client."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client


def get_github_mcp_client() -> GitHubMCPClient:
    """Get or create GitHub MCP client."""
    global _github_mcp_client
    if _github_mcp_client is None:
        _github_mcp_client = GitHubMCPClient()
    return _github_mcp_client