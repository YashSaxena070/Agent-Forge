"""
HashiCorp Vault Integration for Secrets Management
"""
import base64
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import hvac
import hvac.asyncio
from pydantic import BaseModel, Field

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import ExternalServiceError
from apps.backend.src.core.audit import audit_log, AuditEventType, AuditSeverity


class SecretType(str, Enum):
    """Types of secrets managed."""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    SSH_KEY = "ssh_key"
    TLS_CERTIFICATE = "tls_certificate"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_SECRET = "webhook_secret"
    GENERIC = "generic"


class SecretMetadata(BaseModel):
    """Metadata for a secret."""
    secret_id: UUID
    name: str
    secret_type: SecretType
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    rotation_period_days: Optional[int] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    description: str = ""
    owner_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class SecretVersion(BaseModel):
    """A version of a secret."""
    secret_id: UUID
    version: int
    value: str
    created_at: datetime
    created_by: UUID
    is_current: bool = True


@dataclass
class VaultConfig:
    """Vault connection configuration."""
    url: str = "http://localhost:8200"
    token: Optional[str] = None
    namespace: Optional[str] = None
    mount_point: str = "secret"
    kv_version: int = 2
    timeout: int = 30
    verify_ssl: bool = True
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None


class VaultClient:
    """Async HashiCorp Vault client with secret management."""
    
    def __init__(self, config: VaultConfig = None):
        self.config = config or VaultConfig(
            url=settings.VAULT_URL,
            token=settings.VAULT_TOKEN,
            namespace=settings.VAULT_NAMESPACE,
            mount_point=settings.VAULT_MOUNT_POINT,
        )
        self._client: Optional[hvac.asyncio.AsyncClient] = None
        self._initialized = False
    
    async def _get_client(self) -> hvac.asyncio.AsyncClient:
        """Get or create Vault client."""
        if self._client is None:
            self._client = hvac.asyncio.AsyncClient(
                url=self.config.url,
                token=self.config.token,
                namespace=self.config.namespace,
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
            )
        return self._client
    
    async def initialize(self):
        """Initialize and verify Vault connection."""
        client = await self._get_client()
        
        # Test connection
        if not await client.is_authenticated():
            raise ExternalServiceError("vault", "Authentication failed")
        
        # Ensure KV secrets engine is mounted
        mounts = await client.sys.list_mounted_secrets_engines()
        if f"{self.config.mount_point}/" not in mounts:
            await client.sys.enable_secrets_engine(
                backend_type="kv",
                path=self.config.mount_point,
                options={"version": str(self.config.kv_version)},
            )
        
        self._initialized = True
    
    def _secret_path(self, name: str) -> str:
        """Get full path for secret."""
        return f"{self.config.mount_point}/data/{name}"
    
    def _metadata_path(self, name: str) -> str:
        """Get metadata path for secret."""
        return f"{self.config.mount_point}/metadata/{name}"
    
    async def create_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType = SecretType.GENERIC,
        metadata: Dict[str, Any] = None,
        expires_at: datetime = None,
        rotation_period_days: int = None,
    ) -> SecretMetadata:
        """Create a new secret."""
        client = await self._get_client()
        
        secret_data = {
            "value": value,
            "type": secret_type.value,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        
        if expires_at:
            secret_data["expires_at"] = expires_at.isoformat()
        if rotation_period_days:
            secret_data["rotation_period_days"] = rotation_period_days
        
        await client.secrets.kv.v2.create_or_update_secret(
            path=name,
            secret=secret_data,
            mount_point=self.config.mount_point,
        )
        
        # Get created secret metadata
        secret_meta = await self.get_secret_metadata(name)
        
        # Audit log
        await audit_log(
            event_type=AuditEventType.SECRET_ACCESSED,
            action="secret.created",
            resource_type="secret",
            resource_id=secret_meta.secret_id,
            details={"name": name, "type": secret_type.value},
            severity=AuditSeverity.MEDIUM,
            compliance_tags=["secret_management"],
        )
        
        return secret_meta
    
    async def get_secret(self, name: str, version: int = None) -> SecretVersion:
        """Get a secret value."""
        client = await self._get_client()
        
        if version:
            resp = await client.secrets.kv.v2.read_secret_version(
                path=name,
                version=version,
                mount_point=self.config.mount_point,
            )
        else:
            resp = await client.secrets.kv.v2.read_secret_version(
                path=name,
                mount_point=self.config.mount_point,
            )
        
        data = resp["data"]["data"]
        metadata = resp["data"]["metadata"]
        
        return SecretVersion(
            secret_id=UUID(metadata.get("custom_metadata", {}).get("secret_id", str(uuid4()))),
            version=metadata["version"],
            value=data["value"],
            created_at=datetime.fromisoformat(metadata["created_time"]),
            created_by=UUID(data.get("created_by", "00000000-0000-0000-0000-000000000000")),
            is_current=metadata["version"] == metadata.get("current_version", metadata["version"]),
        )
    
    async def update_secret(
        self,
        name: str,
        value: str,
        metadata: Dict[str, Any] = None,
    ) -> SecretMetadata:
        """Update a secret (creates new version)."""
        client = await self._get_client()
        
        # Get current secret to preserve metadata
        current = await self.get_secret(name)
        
        secret_data = {
            "value": value,
            "type": current.value if hasattr(current, 'type') else SecretType.GENERIC.value,
            "metadata": metadata or {},
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        await client.secrets.kv.v2.create_or_update_secret(
            path=name,
            secret=secret_data,
            mount_point=self.config.mount_point,
        )
        
        secret_meta = await self.get_secret_metadata(name)
        
        # Audit log
        await audit_log(
            event_type=AuditEventType.SECRET_ROTATED,
            action="secret.updated",
            resource_type="secret",
            resource_id=secret_meta.secret_id,
            details={"name": name, "new_version": secret_meta.version},
            severity=AuditSeverity.MEDIUM,
            compliance_tags=["secret_management", "rotation"],
        )
        
        return secret_meta
    
    async def delete_secret(self, name: str, permanent: bool = False) -> bool:
        """Delete a secret."""
        client = await self._get_client()
        
        if permanent:
            await client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=name,
                mount_point=self.config.mount_point,
            )
        else:
            await client.secrets.kv.v2.delete_latest_version_of_secret(
                path=name,
                mount_point=self.config.mount_point,
            )
        
        # Audit log
        await audit_log(
            event_type=AuditEventType.SECRET_ACCESSED,
            action="secret.deleted",
            resource_type="secret",
            details={"name": name, "permanent": permanent},
            severity=AuditSeverity.HIGH,
            compliance_tags=["secret_management"],
        )
        
        return True
    
    async def list_secrets(self, prefix: str = "") -> List[str]:
        """List secret names."""
        client = await self._get_client()
        
        resp = await client.secrets.kv.v2.list_secrets(
            path=prefix,
            mount_point=self.config.mount_point,
        )
        
        return resp["data"]["keys"]
    
    async def get_secret_metadata(self, name: str) -> SecretMetadata:
        """Get secret metadata without value."""
        client = await self._get_client()
        
        resp = await client.secrets.kv.v2.read_secret_metadata(
            path=name,
            mount_point=self.config.mount_point,
        )
        
        metadata = resp["data"]
        custom_meta = metadata.get("custom_metadata", {})
        
        return SecretMetadata(
            secret_id=UUID(custom_meta.get("secret_id", str(uuid4()))),
            name=name,
            secret_type=SecretType(custom_meta.get("type", "generic")),
            version=metadata["version"],
            created_at=datetime.fromisoformat(metadata["created_time"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(metadata["updated_time"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(custom_meta["expires_at"]) if custom_meta.get("expires_at") else None,
            rotation_period_days=custom_meta.get("rotation_period_days"),
            tags=custom_meta.get("tags", {}),
            description=custom_meta.get("description", ""),
            owner_id=UUID(custom_meta["owner_id"]) if custom_meta.get("owner_id") else None,
            project_id=UUID(custom_meta["project_id"]) if custom_meta.get("project_id") else None,
        )
    
    async def rotate_secret(
        self,
        name: str,
        new_value: str = None,
        generator: callable = None,
    ) -> SecretMetadata:
        """Rotate a secret with optional generator."""
        if new_value is None and generator is None:
            raise ValueError("Either new_value or generator must be provided")
        
        if generator:
            new_value = await generator()
        
        return await self.update_secret(name, new_value)
    
    async def configure_rotation_policy(
        self,
        name: str,
        rotation_period_days: int,
        generator: callable = None,
    ):
        """Configure automatic rotation for a secret."""
        # In production, this would integrate with Vault's rotation or use a scheduler
        client = await self._get_client()
        
        # Store rotation config in secret metadata
        current_meta = await self.get_secret_metadata(name)
        
        await client.secrets.kv.v2.patch(
            path=self._metadata_path(name),
            mount_point=self.config.mount_point,
            json={
                "custom_metadata": {
                    "rotation_period_days": rotation_period_days,
                    "rotation_generator": generator.__name__ if generator else None,
                    "next_rotation": (datetime.utcnow() + timedelta(days=rotation_period_days)).isoformat(),
                }
            }
        )
    
    async def check_expiring_secrets(self, days_ahead: int = 30) -> List[SecretMetadata]:
        """Check for secrets expiring within specified days."""
        all_secrets = await self.list_secrets()
        expiring = []
        
        threshold = datetime.utcnow() + timedelta(days=days_ahead)
        
        for secret_name in all_secrets:
            meta = await self.get_secret_metadata(secret_name)
            if meta.expires_at and meta.expires_at <= threshold:
                expiring.append(meta)
        
        return expiring
    
    async def close(self):
        """Close Vault client."""
        if self._client:
            await self._client.close()


class SecretManager:
    """High-level secret management with caching and rotation."""
    
    def __init__(self, vault_client: VaultClient = None):
        self.vault = vault_client or VaultClient()
        self._cache: Dict[str, SecretVersion] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def initialize(self):
        await self.vault.initialize()
    
    async def get_secret(
        self,
        name: str,
        use_cache: bool = True,
    ) -> str:
        """Get secret value with caching."""
        if use_cache and name in self._cache:
            cached = self._cache[name]
            cache_age = datetime.utcnow() - self._cache_timestamps[name]
            if cache_age.total_seconds() < self._cache_ttl:
                return cached.value
        
        secret = await self.vault.get_secret(name)
        self._cache[name] = secret
        self._cache_timestamps[name] = datetime.utcnow()
        
        return secret.value
    
    async def get_secret_metadata(self, name: str) -> SecretMetadata:
        return await self.vault.get_secret_metadata(name)
    
    async def create_or_update_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType = SecretType.GENERIC,
        **kwargs,
    ) -> SecretMetadata:
        """Create or update secret."""
        # Invalidate cache
        self._cache.pop(name, None)
        self._cache_timestamps.pop(name, None)
        
        try:
            return await self.vault.update_secret(name, value, **kwargs)
        except Exception:
            # Secret doesn't exist, create it
            return await self.vault.create_secret(name, value, secret_type, **kwargs)
    
    async def rotate_secret(self, name: str, generator: callable = None) -> SecretMetadata:
        """Rotate a secret."""
        self._cache.pop(name, None)
        self._cache_timestamps.pop(name, None)
        
        return await self.vault.rotate_secret(name, generator=generator)
    
    async def get_database_url(self) -> str:
        """Get database URL from Vault."""
        return await self.get_secret("database/url")
    
    async def get_redis_url(self) -> str:
        """Get Redis URL from Vault."""
        return await self.get_secret("redis/url")
    
    async def get_jwt_secret(self) -> str:
        """Get JWT signing secret."""
        return await self.get_secret("jwt/secret")
    
    async def get_encryption_key(self) -> str:
        """Get encryption key."""
        return await self.get_secret("encryption/key")
    
    async def get_llm_api_key(self, provider: str) -> str:
        """Get LLM API key."""
        return await self.get_secret(f"llm/{provider}/api_key")
    
    async def close(self):
        await self.vault.close()


# Global instances
vault_config = VaultConfig()
vault_client = VaultClient(vault_config)
secret_manager = SecretManager(vault_client)


async def get_secret(name: str) -> str:
    """Convenience function to get secret value."""
    return await secret_manager.get_secret(name)


async def get_database_url() -> str:
    """Get database URL from Vault."""
    return await secret_manager.get_database_url()


async def get_redis_url() -> str:
    """Get Redis URL from Vault."""
    return await secret_manager.get_redis_url()