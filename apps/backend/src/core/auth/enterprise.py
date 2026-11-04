"""
Enterprise Authentication - SSO/OIDC/SAML with MFA support.
"""
import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlencode
from uuid import UUID, uuid4

import jwt
import pyotp
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import load_pem_x509_certificate
from passlib.context import CryptContext
from pydantic import BaseModel, Field, HttpUrl
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import AuthenticationError, AuthorizationError
from apps.backend.src.core.database import db_manager
from apps.backend.src.models.entities import User, UserRole, MFAMethod, MFAStatus
from apps.backend.src.core.tools import get_tool_executor


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthProvider(str, Enum):
    LOCAL = "local"
    OIDC = "oidc"
    SAML = "saml"
    LDAP = "ldap"


class MFAType(str, Enum):
    TOTP = "totp"
    WEBAUTHN = "webauthn"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


@dataclass
class OIDCProviderConfig:
    """OpenID Connect provider configuration."""
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    jwks_uri: str = ""
    logout_endpoint: str = ""
    
    @classmethod
    def from_discovery(cls, issuer: str, client_id: str, client_secret: str, redirect_uri: str) -> "OIDCProviderConfig":
        """Fetch configuration from OIDC discovery endpoint."""
        resp = requests.get(f"{issuer.rstrip('/')}/.well-known/openid-configuration", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return cls(
            issuer=issuer,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            authorization_endpoint=data.get("authorization_endpoint", ""),
            token_endpoint=data.get("token_endpoint", ""),
            userinfo_endpoint=data.get("userinfo_endpoint", ""),
            jwks_uri=data.get("jwks_uri", ""),
            logout_endpoint=data.get("end_session_endpoint", ""),
        )


@dataclass
class SAMLProviderConfig:
    """SAML 2.0 provider configuration."""
    entity_id: str
    sso_url: str
    slo_url: str
    x509_cert: str
    acs_url: str
    metadata_url: str = ""
    attribute_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "email": "email",
        "first_name": "firstName",
        "last_name": "lastName",
        "groups": "groups",
    })


class SSOManager:
    """Manages SSO providers and authentication flows."""
    
    def __init__(self):
        self.oidc_providers: Dict[str, OIDCProviderConfig] = {}
        self.saml_providers: Dict[str, SAMLProviderConfig] = {}
        self._jwks_cache: Dict[str, Dict] = {}
        self._jwks_cache_expiry: Dict[str, float] = {}
    
    def register_oidc_provider(self, name: str, config: OIDCProviderConfig):
        """Register an OIDC provider."""
        self.oidc_providers[name] = config
    
    def register_saml_provider(self, name: str, config: SAMLProviderConfig):
        """Register a SAML provider."""
        self.saml_providers[name] = config
    
    def get_oidc_authorization_url(self, provider_name: str, state: str, nonce: str, pkce_challenge: str = None) -> str:
        """Generate OIDC authorization URL."""
        provider = self.oidc_providers.get(provider_name)
        if not provider:
            raise AuthenticationError(f"OIDC provider not found: {provider_name}")
        
        params = {
            "response_type": "code",
            "client_id": provider.client_id,
            "redirect_uri": provider.redirect_uri,
            "scope": " ".join(provider.scopes),
            "state": state,
            "nonce": nonce,
        }
        
        if pkce_challenge:
            params["code_challenge"] = pkce_challenge
            params["code_challenge_method"] = "S256"
        
        return f"{provider.authorization_endpoint}?{urlencode(params)}"
    
    async def exchange_oidc_code(self, provider_name: str, code: str, pkce_verifier: str = None) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        provider = self.oidc_providers.get(provider_name)
        if not provider:
            raise AuthenticationError(f"OIDC provider not found: {provider_name}")
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": provider.redirect_uri,
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        }
        
        if pkce_verifier:
            data["code_verifier"] = pkce_verifier
        
        resp = await self._http_post(provider.token_endpoint, data)
        return resp.json()
    
    async def get_oidc_userinfo(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """Fetch user info from OIDC provider."""
        provider = self.oidc_providers.get(provider_name)
        if not provider:
            raise AuthenticationError(f"OIDC provider not found: {provider_name}")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = await self._http_get(provider.userinfo_endpoint, headers)
        return resp.json()
    
    def get_saml_client(self, provider_name: str) -> Saml2Client:
        """Create SAML client for provider."""
        provider = self.saml_providers.get(provider_name)
        if not provider:
            raise AuthenticationError(f"SAML provider not found: {provider_name}")
        
        config = Saml2Config()
        config.entityid = provider.entity_id
        config.allow_unknown_attributes = True
        config.service.sp = {
            "endpoints": {
                "assertion_consumer_service": [(provider.acs_url, BINDING_HTTP_POST)],
                "single_logout_service": [(provider.slo_url, BINDING_HTTP_REDIRECT)],
            },
            "allow_unsolicited": True,
            "authn_requests_signed": True,
            "logout_requests_signed": True,
            "want_assertions_signed": True,
            "want_response_signed": True,
        }
        config.metadata = {
            "remote": [{"url": provider.metadata_url}] if provider.metadata_url else [],
        }
        config.key_file = ""  # Would be set from private key
        config.cert_file = ""  # Would be set from certificate
        
        return Saml2Client(config)
    
    async def validate_saml_response(self, provider_name: str, saml_response: str) -> Dict[str, Any]:
        """Validate SAML response and extract user attributes."""
        client = self.get_saml_client(provider_name)
        authn_response = client.parse_authn_request_response(
            saml_response,
            BINDING_HTTP_POST,
        )
        
        if not authn_response:
            raise AuthenticationError("Invalid SAML response")
        
        # Extract attributes
        identity = authn_response.get_identity()
        attributes = {}
        provider = self.saml_providers[provider_name]
        for saml_attr, local_attr in provider.attribute_mapping.items():
            if saml_attr in identity:
                attributes[local_attr] = identity[saml_attr][0]
        
        return {
            "name_id": authn_response.get_subject().text,
            "attributes": attributes,
            "session_index": authn_response.session_index(),
        }
    
    async def _get_jwks(self, jwks_uri: str) -> Dict:
        """Fetch and cache JWKS."""
        now = time.time()
        if jwks_uri in self._jwks_cache and self._jwks_cache_expiry.get(jwks_uri, 0) > now:
            return self._jwks_cache[jwks_uri]
        
        resp = await self._http_get(jwks_uri)
        jwks = resp.json()
        self._jwks_cache[jwks_uri] = jwks
        self._jwks_cache_expiry[jwks_uri] = now + 3600  # Cache for 1 hour
        return jwks
    
    def verify_id_token(self, provider_name: str, id_token: str, nonce: str) -> Dict[str, Any]:
        """Verify OIDC ID token signature and claims."""
        provider = self.oidc_providers.get(provider_name)
        if not provider:
            raise AuthenticationError(f"OIDC provider not found: {provider_name}")
        
        # Get signing key
        jwks = asyncio.run(self._get_jwks(provider.jwks_uri))
        header = jwt.get_unverified_header(id_token)
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == header.get("kid"):
                key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                break
        
        if not key:
            raise AuthenticationError("Unable to find signing key")
        
        # Verify and decode
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=provider.client_id,
            issuer=provider.issuer,
        )
        
        # Validate nonce
        if claims.get("nonce") != nonce:
            raise AuthenticationError("Invalid nonce")
        
        return claims
    
    async def _http_get(self, url: str, headers: Dict = None) -> requests.Response:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp
    
    async def _http_post(self, url: str, data: Dict) -> requests.Response:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        return resp


class MFAManager:
    """Multi-factor authentication manager."""
    
    def __init__(self):
        self.issuer = "AgentForge"
    
    def generate_totp_secret(self) -> str:
        """Generate new TOTP secret."""
        return pyotp.random_base32()
    
    def get_totp_uri(self, secret: str, email: str) -> str:
        """Get TOTP provisioning URI for QR code."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=self.issuer,
        )
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for storage."""
        return pwd_context.hash(code)
    
    def verify_backup_code(self, code: str, hashed: str) -> bool:
        """Verify backup code."""
        return pwd_context.verify(code, hashed)
    
    # WebAuthn support (requires webauthn library)
    def generate_webauthn_challenge(self) -> bytes:
        """Generate WebAuthn challenge."""
        return secrets.token_bytes(32)
    
    def verify_webauthn_assertion(self, credential_id: bytes, client_data: bytes, 
                                   authenticator_data: bytes, signature: bytes,
                                   public_key: bytes) -> bool:
        """Verify WebAuthn assertion (placeholder - use webauthn library)."""
        # Implementation would use webauthn library
        return True


class SessionManager:
    """Secure session management with Redis."""
    
    def __init__(self):
        self.session_prefix = "agentforge:session:"
        self.csrf_prefix = "agentforge:csrf:"
        self.default_ttl = settings.JWT_EXPIRATION_HOURS * 3600
    
    async def _get_redis(self):
        import redis.asyncio as redis
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def create_session(
        self,
        user_id: UUID,
        provider: AuthProvider,
        mfa_verified: bool = False,
        metadata: Dict = None,
        ttl: int = None,
    ) -> str:
        """Create new session."""
        redis = await self._get_redis()
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": str(user_id),
            "provider": provider.value,
            "mfa_verified": str(mfa_verified).lower(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "metadata": json.dumps(metadata or {}),
        }
        
        ttl = ttl or self.default_ttl
        pipe = redis.pipeline()
        pipe.hset(f"{self.session_prefix}{session_id}", mapping=session_data)
        pipe.expire(f"{self.session_prefix}{session_id}", ttl)
        # Track user sessions for revocation
        pipe.sadd(f"agentforge:user_sessions:{user_id}", session_id)
        await pipe.execute()
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        redis = await self._get_redis()
        data = await redis.hgetall(f"{self.session_prefix}{session_id}")
        if not data:
            return None
        
        # Update last activity
        await redis.hset(f"{self.session_prefix}{session_id}", "last_activity", 
                        datetime.now(timezone.utc).isoformat())
        
        return data
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        redis = await self._get_redis()
        session_data = await redis.hgetall(f"{self.session_prefix}{session_id}")
        if not session_data:
            return False
        
        user_id = session_data.get("user_id")
        pipe = redis.pipeline()
        pipe.delete(f"{self.session_prefix}{session_id}")
        if user_id:
            pipe.srem(f"agentforge:user_sessions:{user_id}", session_id)
        await pipe.execute()
        return True
    
    async def revoke_all_user_sessions(self, user_id: UUID, except_session: str = None) -> int:
        """Revoke all sessions for a user."""
        redis = await self._get_redis()
        sessions = await redis.smembers(f"agentforge:user_sessions:{user_id}")
        
        if except_session:
            sessions.discard(except_session)
        
        if not sessions:
            return 0
        
        pipe = redis.pipeline()
        for session_id in sessions:
            pipe.delete(f"{self.session_prefix}{session_id}")
        pipe.delete(f"agentforge:user_sessions:{user_id}")
        await pipe.execute()
        
        return len(sessions)
    
    async def get_user_sessions(self, user_id: UUID) -> List[Dict]:
        """Get all active sessions for a user."""
        redis = await self._get_redis()
        session_ids = await redis.smembers(f"agentforge:user_sessions:{user_id}")
        
        sessions = []
        for session_id in session_ids:
            data = await redis.hgetall(f"{self.session_prefix}{session_id}")
            if data:
                data["session_id"] = session_id
                sessions.append(data)
        
        return sessions
    
    async def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        redis = await self._get_redis()
        token = secrets.token_urlsafe(32)
        await redis.setex(f"{self.csrf_prefix}{session_id}", 3600, token)
        return token
    
    async def verify_csrf_token(self, session_id: str, token: str) -> bool:
        """Verify CSRF token."""
        redis = await self._get_redis()
        stored = await redis.get(f"{self.csrf_prefix}{session_id}")
        return secrets.compare_digest(stored or "", token)


class TokenManager:
    """JWT token management with rotation."""
    
    def __init__(self):
        self.private_key = self._load_or_generate_key()
        self.public_key = self.private_key.public_key()
        self.algorithm = "RS256"
        self.access_token_ttl = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        self.refresh_token_ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    
    def _load_or_generate_key(self) -> rsa.RSAPrivateKey:
        """Load or generate RSA key pair."""
        # In production, load from secure storage/HSM
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        roles: List[str],
        permissions: List[str],
        session_id: str,
        mfa_verified: bool = False,
    ) -> str:
        """Create short-lived access token."""
        now = datetime.now(timezone.utc)
        exp = now + self.access_token_ttl
        
        claims = {
            "sub": str(user_id),
            "email": email,
            "roles": roles,
            "permissions": permissions,
            "session_id": session_id,
            "mfa_verified": mfa_verified,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "jti": secrets.token_urlsafe(16),
        }
        
        return jwt.encode(claims, self.private_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: UUID, session_id: str) -> str:
        """Create long-lived refresh token."""
        now = datetime.now(timezone.utc)
        exp = now + self.refresh_token_ttl
        
        claims = {
            "sub": str(user_id),
            "session_id": session_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "jti": secrets.token_urlsafe(16),
        }
        
        return jwt.encode(claims, self.private_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode token."""
        try:
            claims = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
            )
            
            if claims.get("type") != token_type:
                raise AuthenticationError(f"Invalid token type: expected {token_type}")
            
            return claims
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
    
    def rotate_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Rotate access and refresh tokens."""
        claims = self.verify_token(refresh_token, "refresh")
        user_id = UUID(claims["sub"])
        session_id = claims["session_id"]
        
        # In production, fetch user roles/permissions from DB
        access_token = self.create_access_token(user_id, "", [], [], session_id)
        new_refresh_token = self.create_refresh_token(user_id, session_id)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }


# Global instances
sso_manager = SSOManager()
mfa_manager = MFAManager()
session_manager = SessionManager()
token_manager = TokenManager()


async def authenticate_user(
    identifier: str,
    password: str,
    mfa_token: str = None,
    backup_code: str = None,
) -> Dict[str, Any]:
    """Authenticate user with password and optional MFA."""
    async with db_manager.session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == identifier)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationError("Invalid credentials")
        
        if not pwd_context.verify(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        
        # Check MFA
        mfa_verified = False
        if user.mfa_enabled:
            if mfa_token:
                mfa_verified = await verify_mfa(user, mfa_token)
            elif backup_code:
                mfa_verified = await verify_backup_code(user, backup_code)
            else:
                raise AuthenticationError("MFA required")
        
        # Create session
        session_id = await session_manager.create_session(
            user_id=user.id,
            provider=AuthProvider.LOCAL,
            mfa_verified=mfa_verified,
        )
        
        # Get user roles/permissions
        roles = [user.role.value]
        permissions = get_permissions_for_roles(roles)
        
        access_token = token_manager.create_access_token(
            user_id=user.id,
            email=user.email,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            mfa_verified=mfa_verified,
        )
        
        refresh_token = token_manager.create_refresh_token(
            user_id=user.id,
            session_id=session_id,
        )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await session.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(settings.JWT_EXPIRATION_HOURS * 3600),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "mfa_enabled": user.mfa_enabled,
            },
        }


async def verify_mfa(user: User, token: str) -> bool:
    """Verify MFA token for user."""
    async with db_manager.session() as session:
        from sqlalchemy import select
        from apps.backend.src.models.entities import MFAMethod
        
        result = await session.execute(
            select(MFAMethod).where(
                MFAMethod.user_id == user.id,
                MFAMethod.is_active == True,
            )
        )
        methods = result.scalars().all()
        
        for method in methods:
            if method.method_type == MFAType.TOTP:
                secret = method.get_secret()  # Decrypt stored secret
                if mfa_manager.verify_totp(secret, token):
                    return True
            elif method.method_type == MFAType.BACKUP_CODES:
                if mfa_manager.verify_backup_code(token, method.hashed_value):
                    # Mark backup code as used
                    method.mark_used()
                    await session.commit()
                    return True
        
        return False


async def verify_backup_code(user: User, code: str) -> bool:
    """Verify backup code."""
    return await verify_mfa(user, code)  # Same logic


def get_permissions_for_roles(roles: List[str]) -> Set[str]:
    """Get all permissions for roles."""
    from apps.backend.src.core.security import ROLE_PERMISSIONS, Role, Permission
    
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return permissions


import json
import asyncio