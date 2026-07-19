from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.domains.identity.apikey import ApiKeyManager
from aimart.domains.identity.mfa import MfaService
from aimart.domains.identity.models import (
    Agent,
    AgentStatus,
    KycStatus,
    Participant,
    ParticipantStatus,
    ParticipantType,
    SpendingAuthorityLevel,
)
from aimart.domains.identity.oauth2 import OAuth2AgentFlow
from aimart.domains.identity.schemas import (
    AgentDetailResponse,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    GetTokenRequest,
    GetTokenResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    MfaVerifyResponse,
    ParticipantDetailResponse,
    RegisterAgentRequest,
    RegisterAgentResponse,
    RegisterParticipantRequest,
    RegisterParticipantResponse,
)

logger = structlog.get_logger(__name__)

# Password hashing context
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class IdentityService:
    """High-level orchestration for the identity domain.

    All public methods accept an ``AsyncSession`` as the first argument so
    that callers control the transaction boundary.
    """

    def __init__(
        self,
        api_key_manager: ApiKeyManager,
        oauth2_flow: OAuth2AgentFlow,
        mfa_service: MfaService,
    ) -> None:
        self._key_mgr = api_key_manager
        self._oauth2 = oauth2_flow
        self._mfa = mfa_service

    # ------------------------------------------------------------------
    # Participant registration
    # ------------------------------------------------------------------

    async def register_participant(
        self,
        db: AsyncSession,
        request: RegisterParticipantRequest,
    ) -> RegisterParticipantResponse:
        """Register a new participant and issue the initial API key."""
        # Check email uniqueness
        stmt = select(Participant).where(Participant.email == request.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError(f"Email {request.email} is already registered")

        # Hash password
        password_hash = _pwd_context.hash(request.password)

        # Create participant
        participant = Participant(
            type=ParticipantType(request.type),
            name=request.name,
            email=request.email,
            phone=request.phone,
            jurisdiction=request.jurisdiction,
            password_hash=password_hash,
            kyc_status=KycStatus.PENDING,
            status=ParticipantStatus.ACTIVE,
        )
        db.add(participant)
        await db.flush()

        # Generate initial API key
        raw_key, _ = await self._key_mgr.generate(
            db,
            participant_id=participant.id,
            participant_type=participant.type.value,
        )

        # TODO: send verification email via integration layer
        logger.info(
            "identity.register_participant",
            participant_id=str(participant.id),
            type=request.type,
        )

        return RegisterParticipantResponse(
            id=participant.id,
            type=participant.type.value,
            name=participant.name,
            email=participant.email,
            status=participant.status.value,
            created_at=participant.created_at,
            api_key=raw_key,
        )

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    async def register_agent(
        self,
        db: AsyncSession,
        request: RegisterAgentRequest,
        owner_id: uuid.UUID,
    ) -> RegisterAgentResponse:
        """Register a new AI Agent under the given owner."""
        # Validate owner exists and is active
        owner = await db.get(Participant, owner_id)
        if owner is None:
            raise ValueError(f"Owner {owner_id} not found")
        if owner.status != ParticipantStatus.ACTIVE:
            raise ValueError(f"Owner {owner_id} is not active")

        # Compute capability scope hash
        scope_hash: str | None = None
        if request.capability_scope:
            import json

            canonical = json.dumps(request.capability_scope, sort_keys=True)
            scope_hash = hashlib.sha256(canonical.encode()).hexdigest()

        # Create agent
        agent = Agent(
            owner_id=owner_id,
            name=request.name,
            description=request.description,
            framework=request.framework,
            framework_version=request.framework_version,
            capability_scope=request.capability_scope,
            capability_scope_hash=scope_hash,
            spending_authority_level=SpendingAuthorityLevel(
                request.spending_authority_level
            ),
            budget_pool_id=request.budget_pool_id,
            trust_score=50,
            status=AgentStatus.ACTIVE,
        )
        db.add(agent)
        await db.flush()

        # Generate agent-specific API key
        raw_key, _ = await self._key_mgr.generate(
            db,
            participant_id=owner_id,
            participant_type=owner.type.value,
            agent_id=agent.id,
            scopes=request.scopes if hasattr(request, "scopes") else None,
        )

        logger.info(
            "identity.register_agent",
            agent_id=str(agent.id),
            owner_id=str(owner_id),
            framework=request.framework,
        )

        return RegisterAgentResponse(
            id=agent.id,
            owner_id=agent.owner_id,
            name=agent.name,
            framework=agent.framework.value,
            spending_authority_level=agent.spending_authority_level.value,
            trust_score=agent.trust_score,
            status=agent.status.value,
            created_at=agent.created_at,
            api_key=raw_key,
        )

    # ------------------------------------------------------------------
    # Token issuance (OAuth2 client_credentials)
    # ------------------------------------------------------------------

    async def get_token(
        self,
        db: AsyncSession,
        request: GetTokenRequest,
        api_key_info: dict[str, Any],
    ) -> GetTokenResponse:
        """Exchange a verified API key for OAuth2 tokens."""
        requested_scopes = request.scope.split() if request.scope else None
        result = await self._oauth2.client_credentials_grant(
            db,
            api_key_info=api_key_info,
            requested_scopes=requested_scopes,
        )
        return GetTokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            refresh_token=result.get("refresh_token"),
            scope=result["scope"],
        )

    # ------------------------------------------------------------------
    # Agent termination (high-risk – requires MFA)
    # ------------------------------------------------------------------

    async def terminate_agent(
        self,
        db: AsyncSession,
        agent_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """Terminate an agent: freeze, revoke keys, mark terminated.

        The caller is responsible for MFA verification before calling this.
        """
        agent = await db.get(Agent, agent_id)
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        if agent.owner_id != owner_id:
            raise PermissionError("Only the agent owner can terminate it")
        if agent.status == AgentStatus.TERMINATED:
            raise ValueError(f"Agent {agent_id} is already terminated")

        # TODO: freeze open orders via exchange domain integration
        logger.info(
            "identity.terminate_agent.freezing_orders",
            agent_id=str(agent_id),
        )

        # Revoke all API keys for this agent
        revoked_count = await self._key_mgr.revoke_all_for_agent(
            db, agent_id=agent_id, reason="agent_terminated"
        )

        # Mark agent terminated
        now = datetime.now(UTC)
        agent.status = AgentStatus.TERMINATED
        agent.updated_at = now
        await db.flush()

        logger.info(
            "identity.terminate_agent",
            agent_id=str(agent_id),
            revoked_keys=revoked_count,
        )

    # ------------------------------------------------------------------
    # Detail lookups
    # ------------------------------------------------------------------

    async def get_participant(
        self,
        db: AsyncSession,
        participant_id: uuid.UUID,
    ) -> ParticipantDetailResponse:
        participant = await db.get(Participant, participant_id)
        if participant is None:
            raise ValueError(f"Participant {participant_id} not found")

        return ParticipantDetailResponse(
            id=participant.id,
            type=participant.type.value,
            name=participant.name,
            email=participant.email,
            email_verified=participant.email_verified,
            phone=participant.phone,
            phone_verified=participant.phone_verified,
            jurisdiction=participant.jurisdiction,
            kyc_status=participant.kyc_status.value,
            mfa_enabled=participant.mfa_enabled,
            status=participant.status.value,
            created_at=participant.created_at,
            updated_at=participant.updated_at,
        )

    async def get_agent(
        self,
        db: AsyncSession,
        agent_id: uuid.UUID,
    ) -> AgentDetailResponse:
        agent = await db.get(Agent, agent_id)
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")

        return AgentDetailResponse(
            id=agent.id,
            owner_id=agent.owner_id,
            name=agent.name,
            description=agent.description,
            framework=agent.framework.value,
            framework_version=agent.framework_version,
            capability_scope=agent.capability_scope,
            spending_authority_level=agent.spending_authority_level.value,
            budget_pool_id=agent.budget_pool_id,
            trust_score=agent.trust_score,
            trust_score_updated_at=agent.trust_score_updated_at,
            last_active_at=agent.last_active_at,
            total_transactions=agent.total_transactions,
            total_spent_cny=agent.total_spent_cny,
            status=agent.status.value,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    # ------------------------------------------------------------------
    # API Key management
    # ------------------------------------------------------------------

    async def create_api_key(
        self,
        db: AsyncSession,
        request: ApiKeyCreateRequest,
        participant_id: uuid.UUID,
        participant_type: str,
    ) -> ApiKeyCreateResponse:
        raw_key, record = await self._key_mgr.generate(
            db,
            participant_id=participant_id,
            participant_type=participant_type,
            agent_id=request.agent_id,
            scopes=request.scopes,
            permissions=request.permissions,
            expires_at=request.expires_at,
            allowed_ips=request.allowed_ips,
            allowed_origins=request.allowed_origins,
        )
        return ApiKeyCreateResponse(
            id=record.id,
            key=raw_key,
            key_prefix=record.key_prefix,
            scopes=record.scopes or [],
            expires_at=record.expires_at,
            created_at=record.created_at,
        )

    async def revoke_api_key(
        self,
        db: AsyncSession,
        key_id: uuid.UUID,
        revoked_by: uuid.UUID,
        reason: str | None = None,
    ) -> None:
        await self._key_mgr.revoke(
            db, key_id=key_id, revoked_by=revoked_by, reason=reason
        )

    # ------------------------------------------------------------------
    # MFA
    # ------------------------------------------------------------------

    async def setup_totp(
        self,
        db: AsyncSession,
        participant_id: uuid.UUID,
    ) -> MfaSetupResponse:
        result = await self._mfa.setup_totp(db, participant_id=participant_id)
        return MfaSetupResponse(
            secret=result["secret"],
            qr_url=result["qr_url"],
            backup_codes=result["backup_codes"],
        )

    async def create_mfa_challenge(
        self,
        db: AsyncSession,
        *,
        participant_id: uuid.UUID,
        purpose: str,
        reference_id: uuid.UUID | None = None,
        challenge_type: str = "totp",
    ) -> dict[str, Any]:
        return await self._mfa.create_challenge(
            db,
            participant_id=participant_id,
            purpose=purpose,
            reference_id=reference_id,
            challenge_type=challenge_type,
        )

    async def verify_mfa_challenge(
        self,
        db: AsyncSession,
        request: MfaVerifyRequest,
    ) -> MfaVerifyResponse:
        verified, message = await self._mfa.verify_challenge(
            db,
            challenge_id=request.challenge_id,
            code=request.code,
        )
        return MfaVerifyResponse(verified=verified, message=message)
