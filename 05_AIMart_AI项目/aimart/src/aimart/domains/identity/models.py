from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimart.db.base import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ParticipantType(enum.StrEnum):
    OWNER = "owner"
    PROVIDER = "provider"
    CERTIFIER = "certifier"
    FACILITATOR = "facilitator"


class KycStatus(enum.StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ParticipantStatus(enum.StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class AgentFramework(enum.StrEnum):
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    DIFY = "dify"
    COZE = "coze"
    CUSTOM = "custom"


class SpendingAuthorityLevel(enum.StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class AgentStatus(enum.StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class ApiKeyStatus(enum.StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class MfaChallengeType(enum.StrEnum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    WEBHOOK = "webhook"


class MfaPurpose(enum.StrEnum):
    AGENT_TERMINATE = "agent_terminate"
    L3_CONFIRM = "l3_confirm"
    KEY_REVOKE = "key_revoke"


class MfaChallengeStatus(enum.StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class OAuth2ClientStatus(enum.StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class RefreshTokenStatus(enum.StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    USED = "used"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[ParticipantType] = mapped_column(
        String(32), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kyc_status: Mapped[KycStatus] = mapped_column(
        String(32),
        nullable=False,
        default=KycStatus.PENDING,
    )
    kyc_documents: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    kyc_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="AES-256-GCM encrypted TOTP secret"
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ParticipantStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    # relationships
    agents: Mapped[list[Agent]] = relationship(
        "Agent", back_populates="owner", lazy="selectin"
    )
    api_keys: Mapped[list[ApiKey]] = relationship(
        "ApiKey", back_populates="participant", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_participants_type_status", "type", "status"),
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    framework: Mapped[AgentFramework] = mapped_column(
        String(32), nullable=False
    )
    framework_version: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    capability_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    capability_scope_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="SHA-256 hash of capability_scope JSON"
    )
    spending_authority_level: Mapped[SpendingAuthorityLevel] = mapped_column(
        String(32),
        nullable=False,
        default=SpendingAuthorityLevel.L0,
    )
    budget_pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    trust_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50
    )
    trust_score_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    total_transactions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    total_spent_cny: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    status: Mapped[AgentStatus] = mapped_column(
        String(32),
        nullable=False,
        default=AgentStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    # relationships
    owner: Mapped[Participant] = relationship(
        "Participant", back_populates="agents"
    )

    __table_args__ = (
        Index("ix_agents_owner_status", "owner_id", "status"),
        Index("ix_agents_trust_score", "trust_score"),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="SHA-512 hash"
    )
    key_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted raw key"
    )
    scopes: Mapped[list | None] = mapped_column(
        JSONB, nullable=False, default=list
    )
    permissions: Mapped[dict | None] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allowed_ips: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    allowed_origins: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    status: Mapped[ApiKeyStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ApiKeyStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    participant: Mapped[Participant] = relationship(
        "Participant", back_populates="api_keys"
    )

    __table_args__ = (
        Index("ix_api_keys_participant_status", "participant_id", "status"),
        Index("ix_api_keys_prefix_hash", "key_prefix", "key_hash"),
    )


class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    client_secret_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="SHA-512 hash"
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grant_types: Mapped[list | None] = mapped_column(
        JSONB, nullable=False, default=list
    )
    redirect_uris: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    scopes: Mapped[list | None] = mapped_column(
        JSONB, nullable=False, default=list
    )
    status: Mapped[OAuth2ClientStatus] = mapped_column(
        String(32),
        nullable=False,
        default=OAuth2ClientStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="SHA-512 hash"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    oauth2_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oauth2_clients.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[RefreshTokenStatus] = mapped_column(
        String(32),
        nullable=False,
        default=RefreshTokenStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_refresh_tokens_participant_status", "participant_id", "status"),
    )


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    challenge_type: Mapped[MfaChallengeType] = mapped_column(
        String(32), nullable=False
    )
    purpose: Mapped[MfaPurpose] = mapped_column(
        String(32), nullable=False
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    status: Mapped[MfaChallengeStatus] = mapped_column(
        String(32),
        nullable=False,
        default=MfaChallengeStatus.PENDING,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_mfa_challenges_participant_status", "participant_id", "status"),
        Index("ix_mfa_challenges_expires", "expires_at"),
    )
