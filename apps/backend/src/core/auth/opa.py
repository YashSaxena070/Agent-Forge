"""
OPA (Open Policy Agent) integration for fine-grained ABAC authorization.
"""
import json
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import AuthorizationError


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""
    decision: Decision
    reason: str = ""
    obligations: List[Dict[str, Any]] = None
    advice: List[Dict[str, Any]] = None


class PolicyInput(BaseModel):
    """Input for policy evaluation."""
    # Subject (who)
    subject: Dict[str, Any] = Field(default_factory=dict)
    # Action (what)
    action: str = ""
    # Resource (on what)
    resource: Dict[str, Any] = Field(default_factory=dict)
    # Context (environment)
    context: Dict[str, Any] = Field(default_factory=dict)


class OPAPolicy:
    """Represents an OPA policy bundle."""
    name: str
    version: str
    rules: str  # Rego source
    data: Dict[str, Any] = None
    
    def __init__(self, name: str, version: str, rules: str, data: Dict = None):
        self.name = name
        self.version = version
        self.rules = rules
        self.data = data or {}


class OPAClient:
    """Client for communicating with OPA."""
    
    def __init__(self, url: str = None, token: str = None):
        self.url = url or settings.OPA_URL
        self.token = token or settings.OPA_TOKEN
        self._client: Optional[httpx.AsyncClient] = None
        self._policy_cache: Dict[str, str] = {}
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.url,
                headers=headers,
                timeout=10.0,
            )
        return self._client
    
    async def evaluate(
        self,
        policy_path: str,
        input_data: Dict[str, Any],
        unknowns: List[str] = None,
    ) -> PolicyDecision:
        """Evaluate a policy decision."""
        client = await self._get_client()
        
        payload = {
            "input": input_data,
        }
        if unknowns:
            payload["unknowns"] = unknowns
        
        try:
            resp = await client.post(
                f"/v1/data/{policy_path.lstrip('/')}",
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            
            decision = result.get("result", {})
            
            # Handle different response formats
            if isinstance(decision, bool):
                return PolicyDecision(
                    decision=Decision.ALLOW if decision else Decision.DENY,
                )
            elif isinstance(decision, dict):
                return PolicyDecision(
                    decision=Decision(decision.get("decision", "deny")),
                    reason=decision.get("reason", ""),
                    obligations=decision.get("obligations"),
                    advice=decision.get("advice"),
                )
            
            return PolicyDecision(decision=Decision.DENY, reason="Invalid policy response")
            
        except httpx.HTTPError as e:
            raise AuthorizationError(f"OPA evaluation failed: {e}")
    
    async def compile_policy(self, rego: str) -> str:
        """Compile Rego policy and return bundle."""
        client = await self._get_client()
        
        resp = await client.post(
            "/v1/compile",
            json={"query": "data", "module": rego},
        )
        resp.raise_for_status()
        return resp.json().get("result", {}).get("bundle", "")
    
    async def health_check(self) -> bool:
        """Check OPA health."""
        try:
            client = await self._get_client()
            resp = await client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        if self._client:
            await self._client.aclose()


class PolicyManager:
    """Manages policies and evaluates authorization decisions."""
    
    # Default policies embedded as Rego
    DEFAULT_POLICIES = {
        "rbac": """
package agentforge.authz

default allow = false

# Allow if user has required role
allow {
    input.action == "read"
    input.subject.roles[_] == "admin"
}

allow {
    input.action == "write"
    input.subject.roles[_] == "admin"
}

allow {
    input.action == "read"
    input.subject.roles[_] == "developer"
    input.resource.owner == input.subject.user_id
}

allow {
    input.action == "write"
    input.subject.roles[_] == "developer"
    input.resource.owner == input.subject.user_id
}

allow {
    input.action == "read"
    input.subject.roles[_] == "viewer"
    input.resource.visibility == "public"
}

# Deny by default
deny {
    not allow
}

# Reason for denial
reason = "Insufficient permissions" {
    deny
}
""",
        
        "project_access": """
package agentforge.project

default allow = false

# Project owner has full access
allow {
    input.action in ["read", "write", "delete", "manage"]
    input.resource.project.owner == input.subject.user_id
}

# Project members have access based on role
allow {
    input.action == "read"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role in ["owner", "developer", "viewer"]
}

allow {
    input.action == "write"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role in ["owner", "developer"]
}

allow {
    input.action == "manage"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role == "owner"
}

# Public projects readable by all
allow {
    input.action == "read"
    input.resource.project.visibility == "public"
}
""",
        
        "workflow_execution": """
package agentforge.workflow

default allow = false

# Workflow owner can execute
allow {
    input.action in ["execute", "pause", "resume", "cancel"]
    input.resource.workflow.project.owner == input.subject.user_id
}

# Project developers can execute workflows
allow {
    input.action in ["execute", "pause", "resume"]
    input.subject.user_id in input.resource.workflow.project.members[_].user_id
    input.resource.workflow.project.members[_].role in ["owner", "developer"]
}

# Approvers can approve/reject
allow {
    input.action == "approve"
    input.subject.user_id in input.resource.workflow.project.members[_].user_id
    input.resource.workflow.project.members[_].role in ["owner", "operator"]
}
""",
        
        "deployment": """
package agentforge.deployment

default allow = false

# Deployment to production requires approval
allow {
    input.action == "deploy"
    input.resource.environment != "production"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role in ["owner", "developer", "devops"]
}

allow {
    input.action == "deploy"
    input.resource.environment == "production"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role in ["owner", "devops"]
    input.context.approval_granted == true
}

# Rollback permissions
allow {
    input.action == "rollback"
    input.subject.user_id in input.resource.project.members[_].user_id
    input.resource.project.members[_].role in ["owner", "devops", "operator"]
}
""",
        
        "data_protection": """
package agentforge.data

default allow = false

# PII access requires explicit permission
allow {
    input.action == "read"
    input.resource.data_classification == "public"
}

allow {
    input.action == "read"
    input.resource.data_classification == "internal"
    input.subject.roles[_] in ["admin", "developer", "viewer"]
    input.subject.clearance_level >= input.resource.required_clearance
}

allow {
    input.action == "read"
    input.resource.data_classification in ["confidential", "restricted"]
    input.subject.roles[_] in ["admin", "security"]
    input.subject.clearance_level >= input.resource.required_clearance
    input.context.purpose in ["audit", "incident_response", "compliance"]
}

# Write access
allow {
    input.action == "write"
    input.resource.data_classification != "restricted"
    input.subject.roles[_] in ["admin", "developer"]
    input.resource.project.owner == input.subject.user_id
}
""",
    }
    
    def __init__(self, opa_client: OPAClient = None):
        self.opa = opa_client or OPAClient()
        self._policies_loaded = False
    
    async def initialize(self):
        """Load default policies into OPA."""
        if self._policies_loaded:
            return
        
        for name, rego in self.DEFAULT_POLICIES.items():
            await self._load_policy(name, rego)
        
        self._policies_loaded = True
    
    async def _load_policy(self, name: str, rego: str):
        """Load a policy into OPA."""
        client = await self.opa._get_client()
        
        # Load as data document
        resp = await client.put(
            f"/v1/policies/{name}",
            content=rego.encode(),
            headers={"Content-Type": "text/plain"},
        )
        resp.raise_for_status()
    
    async def check_permission(
        self,
        user_id: UUID,
        roles: List[str],
        permissions: List[str],
        action: str,
        resource: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> PolicyDecision:
        """Check if user has permission for action on resource."""
        input_data = PolicyInput(
            subject={
                "user_id": str(user_id),
                "roles": roles,
                "permissions": permissions,
            },
            action=action,
            resource=resource,
            context=context or {},
        )
        
        # Determine which policy to use based on resource type
        policy_path = self._get_policy_path(resource)
        
        return await self.opa.evaluate(policy_path, input_data.model_dump())
    
    def _get_policy_path(self, resource: Dict[str, Any]) -> str:
        """Determine policy path based on resource."""
        resource_type = resource.get("type", "")
        
        if resource_type == "project":
            return "agentforge.project"
        elif resource_type == "workflow":
            return "agentforge.workflow"
        elif resource_type == "deployment":
            return "agentforge.deployment"
        elif resource_type in ["data", "document", "file"]:
            return "agentforge.data"
        
        return "agentforge.authz"
    
    async def check_multiple(
        self,
        checks: List[Dict[str, Any]],
    ) -> List[PolicyDecision]:
        """Check multiple permissions in batch."""
        results = []
        for check in checks:
            decision = await self.check_permission(**check)
            results.append(decision)
        return results


class AuthorizationMiddleware:
    """FastAPI middleware for automatic authorization."""
    
    def __init__(self, policy_manager: PolicyManager):
        self.policy_manager = policy_manager
    
    async def authorize(
        self,
        token_data: Dict[str, Any],
        action: str,
        resource: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> PolicyDecision:
        """Authorize a request."""
        return await self.policy_manager.check_permission(
            user_id=UUID(token_data["sub"]),
            roles=token_data.get("roles", []),
            permissions=token_data.get("permissions", []),
            action=action,
            resource=resource,
            context=context,
        )
    
    def require_permission(self, action: str, resource_type: str):
        """Decorator for endpoint authorization."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract token_data from request (would be injected by auth middleware)
                # This is a simplified version
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Global instances
opa_client = OPAClient()
policy_manager = PolicyManager(opa_client)
authz_middleware = AuthorizationMiddleware(policy_manager)


async def require_permission(
    token_data: Dict[str, Any],
    action: str,
    resource: Dict[str, Any],
    context: Dict[str, Any] = None,
) -> PolicyDecision:
    """Convenience function for permission checks."""
    return await policy_manager.check_permission(
        user_id=UUID(token_data["sub"]),
        roles=token_data.get("roles", []),
        permissions=token_data.get("permissions", []),
        action=action,
        resource=resource,
        context=context,
    )


def require_permission_sync(
    token_data: Dict[str, Any],
    action: str,
    resource: Dict[str, Any],
) -> bool:
    """Synchronous permission check (for non-async contexts)."""
    # This would use a sync OPA client or cached decisions
    # For now, return True if admin
    if "admin" in token_data.get("roles", []):
        return True
    return False