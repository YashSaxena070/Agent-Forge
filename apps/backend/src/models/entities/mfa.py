"""
MFA (Multi-Factor Authentication) Models
"""
import enum
import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Boolean,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.src.core.database import Base


class MFAType(str, enum.Enum):
    TOTP = "totp"
    WEBAUTHN = "webauthn"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


class MFAStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_SETUP = "pending_setup"
    LOCKED = "locked"


class MFAMethod(Base):
    """MFA method configuration for a user."""
    __tablename__ = "mfa_methods"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    method_type: Mapped[MFAType] = mapped_column(Enum(MFAType), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # User-friendly name
    status: Mapped[MFAStatus] = mapped_column(Enum(MFAStatus), default=MFAStatus.PENDING_SETUP, nullable=False)
    
    # Encrypted secret storage (TOTP secret, WebAuthn credential ID, etc.)
    encrypted_secret: Mapped[str] = mapped_column(Text, nullable=True)
    secret_iv: Mapped[str] = mapped_column(String(64), nullable=True)  # IV for decryption
    
    # For backup codes: hashed codes stored as JSON array
    hashed_values: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    used_codes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # WebAuthn specific
    credential_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, index=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=True)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    aaguid: Mapped[str] = mapped_column(String(36), nullable=True)
    
    # SMS/Email
    contact_value: Mapped[str] = mapped_column(String(255), nullable=True)  # Phone/email
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mfa_methods")
    
    __table_args__ = (
        Index("ix_mfa_user_type", "user_id", "method_type"),
    )
    
    def get_secret(self) -> str:
        """Decrypt and return the secret (TOTP)."""
        if not self.encrypted_secret:
            return None
        
        from apps.backend.src.core.config import settings
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        key = settings.ENCRYPTION_KEY.encode()[:32]  # 32 bytes for AES-256
        aesgcm = AESGCM(key)
        
        iv = bytes.fromhex(self.secret_iv)
        ciphertext = bytes.fromhex(self.encrypted_secret)
        
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext.decode()
    
    def set_secret(self, secret: str):
        """Encrypt and store the secret (TOTP)."""
        from apps.backend.src.core.config import settings
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import secrets
        
        key = settings.ENCRYPTION_KEY.encode()[:32]
        aesgcm = AESGCM(key)
        
        iv = secrets.token_bytes(12)
        plaintext = secret.encode()
        
        ciphertext = aesgcm.encrypt(iv, plaintext, None)
        
        self.encrypted_secret = ciphertext.hex()
        self.secret_iv = iv.hex()
    
    def add_backup_codes(self, codes: list):
        """Add backup codes (hash them)."""
        from apps.backend.src.core.security import get_password_hash
        
        self.hashed_values = [get_password_hash(code) for code in codes]
        self.used_codes = []
    
    def verify_backup_code(self, code: str) -> bool:
        """Verify and mark backup code as used."""
        from apps.backend.src.core.security import verify_password
        
        for i, hashed in enumerate(self.hashed_values):
            if verify_password(code, hashed) and i not in self.used_codes:
                self.used_codes.append(i)
                return True
        return False
    
    def mark_used(self):
        """Increment sign count for WebAuthn."""
        self.sign_count += 1
        self.last_used_at = datetime.utcnow()
    
    def increment_failed_attempts(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """Increment failed attempts, lock if threshold reached."""
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.status = MFAStatus.LOCKED
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
    
    def reset_failed_attempts(self):
        """Reset failed attempts counter."""
        self.failed_attempts = 0
        self.locked_until = None
        if self.status == MFAStatus.LOCKED:
            self.status = MFAStatus.ACTIVE


class UserSession(Base):
    """User session tracking for security monitoring."""
    __tablename__ = "user_sessions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # local, oidc, saml
    
    # Device info
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 max length
    country: Mapped[str] = mapped_column(String(2), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Security
    mfa_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index("ix_user_sessions_user_active", "user_id", "is_active"),
        Index("ix_user_sessions_expires", "expires_at"),
    )


class LoginAttempt(Base):
    """Track login attempts for security monitoring."""
    __tablename__ = "login_attempts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Track even for non-existent users
    
    # Attempt details
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Context
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=True)
    
    # MFA
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_method: Mapped[str] = mapped_column(String(50), nullable=True)
    mfa_success: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Risk
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_login_attempts_email_time", "email", "created_at"),
        Index("ix_login_attempts_ip_time", "ip_address", "created_at"),
    )


from datetime import timedelta