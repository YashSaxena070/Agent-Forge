"""
Security utilities: JWT authentication, password hashing, RBAC.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Set
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from apps.backend.src.core.config import settings
from services.shared.exceptions import AuthenticationError, AuthorizationError


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# JWT token models
class TokenData(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    roles: List[str] = []
    permissions: List[str] = []
    exp: int
    iat: int
    type: str = "access"


class Token(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# Role-based access control
class Role(str):
    """User roles."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    OPERATOR = "operator"


class Permission(str):
    """System permissions."""
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_LIST = "project:list"
    
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_APPROVE = "workflow:approve"
    
    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_EXECUTE = "agent:execute"
    
    # Deployment permissions
    DEPLOYMENT_CREATE = "deployment:create"
    DEPLOYMENT_READ = "deployment:read"
    DEPLOYMENT_EXECUTE = "deployment:execute"
    DEPLOYMENT_ROLLBACK = "deployment:rollback"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_METRICS = "admin:metrics"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE, Permission.PROJECT_LIST,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE,
        Permission.WORKFLOW_DELETE, Permission.WORKFLOW_EXECUTE, Permission.WORKFLOW_APPROVE,
        Permission.AGENT_READ, Permission.AGENT_EXECUTE,
        Permission.DEPLOYMENT_CREATE, Permission.DEPLOYMENT_READ, Permission.DEPLOYMENT_EXECUTE,
        Permission.DEPLOYMENT_ROLLBACK,
        Permission.ADMIN_USERS, Permission.ADMIN_SYSTEM, Permission.ADMIN_METRICS,
    },
    Role.DEVELOPER: {
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_LIST,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE,
        Permission.WORKFLOW_EXECUTE,
        Permission.AGENT_READ, Permission.AGENT_EXECUTE,
        Permission.DEPLOYMENT_CREATE, Permission.DEPLOYMENT_READ, Permission.DEPLOYMENT_EXECUTE,
    },
    Role.OPERATOR: {
        Permission.PROJECT_READ, Permission.PROJECT_LIST,
        Permission.WORKFLOW_READ, Permission.WORKFLOW_EXECUTE, Permission.WORKFLOW_APPROVE,
        Permission.AGENT_READ,
        Permission.DEPLOYMENT_READ, Permission.DEPLOYMENT_EXECUTE, Permission.DEPLOYMENT_ROLLBACK,
        Permission.ADMIN_METRICS,
    },
    Role.VIEWER: {
        Permission.PROJECT_READ, Permission.PROJECT_LIST,
        Permission.WORKFLOW_READ,
        Permission.AGENT_READ,
        Permission.DEPLOYMENT_READ,
    },
}


def get_permissions_for_roles(roles: List[str]) -> Set[Permission]:
    """Get all permissions for a list of roles."""
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return permissions


def create_access_token(
    subject: UUID,
    email: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    
    permissions = get_permissions_for_roles(roles)
    
    payload = {
        "sub": str(subject),
        "email": email,
        "roles": roles,
        "permissions": list(permissions),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS))
    
    payload = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenData(**payload)
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify token and check type."""
    token_data = decode_token(token)
    if token_data.type != token_type:
        raise AuthenticationError(f"Invalid token type: expected {token_type}")
    return token_data


def create_token_pair(user_id: UUID, email: str, roles: List[str]) -> Token:
    """Create access and refresh token pair."""
    access_token = create_access_token(user_id, email, roles)
    refresh_token = create_refresh_token(user_id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


def refresh_access_token(refresh_token: str, roles: List[str], email: str) -> Token:
    """Create new access token from refresh token."""
    token_data = verify_token(refresh_token, "refresh")
    user_id = UUID(token_data.sub)
    
    return create_token_pair(user_id, email, roles)


# Permission checking
def check_permission(token_data: TokenData, permission: Permission) -> bool:
    """Check if token has specific permission."""
    return permission in token_data.permissions


def require_permission(token_data: TokenData, permission: Permission) -> None:
    """Raise AuthorizationError if permission not granted."""
    if not check_permission(token_data, permission):
        raise AuthorizationError(f"Permission required: {permission}")


def require_any_permission(token_data: TokenData, permissions: List[Permission]) -> None:
    """Raise AuthorizationError if none of the permissions granted."""
    if not any(check_permission(token_data, p) for p in permissions):
        raise AuthorizationError(f"One of these permissions required: {permissions}")


def require_role(token_data: TokenData, role: Role) -> None:
    """Raise AuthorizationError if role not granted."""
    if role not in token_data.roles:
        raise AuthorizationError(f"Role required: {role}")


def require_any_role(token_data: TokenData, roles: List[Role]) -> None:
    """Raise AuthorizationError if none of the roles granted."""
    if not any(r in token_data.roles for r in roles):
        raise AuthorizationError(f"One of these roles required: {roles}")


# API Key management
class APIKey(BaseModel):
    """API Key model."""
    key: str
    name: str
    hashed_key: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime] = None


def generate_api_key() -> str:
    """Generate a new API key."""
    import secrets
    return f"af_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return get_password_hash(key)


def verify_api_key(key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return verify_password(key, hashed_key)