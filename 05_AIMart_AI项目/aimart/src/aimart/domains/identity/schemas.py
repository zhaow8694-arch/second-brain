from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Register Participant
# ---------------------------------------------------------------------------

class RegisterParticipantRequest(BaseModel):
    type: str = Field(..., pattern=r"^(owner|provider|certifier|facilitator)$")
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: str | None = Field(None, max_length=32)
    jurisdiction: str | None = Field(None, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterParticipantResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    email: str
    status: str
    created_at: datetime
    api_key: str = Field(..., description="Initial API key – shown only once")


# ---------------------------------------------------------------------------
# Register Agent
# ---------------------------------------------------------------------------

class RegisterAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    framework: str = Field(
        ..., pattern=r"^(langchain|crewai|autogen|dify|coze|custom)$"
    )
    framework_version: str | None = Field(None, max_length=32)
    capability_scope: dict[str, Any] | None = None
    spending_authority_level: str = Field(
        "L0", pattern=r"^(L0|L1|L2|L3)$"
    )
    budget_pool_id: uuid.UUID | None = None


class RegisterAgentResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    framework: str
    spending_authority_level: str
    trust_score: int
    status: str
    created_at: datetime
    api_key: str = Field(..., description="Agent API key – shown only once")


# ---------------------------------------------------------------------------
# Get Token (OAuth2 client_credentials)
# ---------------------------------------------------------------------------

class GetTokenRequest(BaseModel):
    grant_type: str = Field("client_credentials", pattern=r"^client_credentials$")
    scope: str | None = None


class GetTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str


# ---------------------------------------------------------------------------
# Participant Detail
# ---------------------------------------------------------------------------

class ParticipantDetailResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    email: str
    email_verified: bool
    phone: str | None
    phone_verified: bool
    jurisdiction: str | None
    kyc_status: str
    mfa_enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Agent Detail
# ---------------------------------------------------------------------------

class AgentDetailResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    framework: str
    framework_version: str | None
    capability_scope: dict[str, Any] | None
    spending_authority_level: str
    budget_pool_id: uuid.UUID | None
    trust_score: int
    trust_score_updated_at: datetime | None
    last_active_at: datetime | None
    total_transactions: int
    total_spent_cny: float
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# API Key Create
# ---------------------------------------------------------------------------

class ApiKeyCreateRequest(BaseModel):
    agent_id: uuid.UUID | None = None
    scopes: list[str] | None = None
    permissions: dict[str, Any] | None = None
    expires_at: datetime | None = None
    allowed_ips: list[str] | None = None
    allowed_origins: list[str] | None = None


class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    key: str = Field(..., description="Raw API key – shown only once")
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


# ---------------------------------------------------------------------------
# MFA
# ---------------------------------------------------------------------------

class MfaSetupResponse(BaseModel):
    secret: str
    qr_url: str
    backup_codes: list[str]


class MfaVerifyRequest(BaseModel):
    challenge_id: uuid.UUID
    code: str = Field(..., min_length=6, max_length=8)


class MfaVerifyResponse(BaseModel):
    verified: bool
    message: str
