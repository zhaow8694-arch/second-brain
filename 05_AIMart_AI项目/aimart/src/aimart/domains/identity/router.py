from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.db.session import get_db
from aimart.domains.identity.apikey import ApiKeyManager
from aimart.domains.identity.auth import (
    AuthContext,
    require_auth,
    require_owner,
)
from aimart.domains.identity.mfa import MfaService
from aimart.domains.identity.models import (
    MfaChallenge,
    MfaChallengeStatus,
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
from aimart.domains.identity.service import IdentityService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["identity"])

# ---------------------------------------------------------------------------
# Service singletons (wired via lifespan in main app)
# ---------------------------------------------------------------------------

_api_key_manager = ApiKeyManager()
_oauth2_flow = OAuth2AgentFlow()
_mfa_service = MfaService()
_service = IdentityService(
    api_key_manager=_api_key_manager,
    oauth2_flow=_oauth2_flow,
    mfa_service=_mfa_service,
)


def _get_service() -> IdentityService:
    return _service


# ---------------------------------------------------------------------------
# Helper: extract API key info from auth context for token endpoint
# ---------------------------------------------------------------------------

async def _resolve_api_key_info(request: Request) -> dict[str, Any]:
    """Extract the raw API key from the request and verify it."""
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required for token endpoint",
        )
    key_info = await _api_key_manager.verify(raw_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    return key_info


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=RegisterParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_participant(
    request: RegisterParticipantRequest,
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> RegisterParticipantResponse:
    """Register a new participant (owner / provider / certifier / facilitator)."""
    try:
        return await svc.register_participant(db, request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/agents",
    response_model=RegisterAgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_agent(
    request: RegisterAgentRequest,
    ctx: AuthContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> RegisterAgentResponse:
    """Register a new AI Agent under the authenticated owner."""
    try:
        return await svc.register_agent(db, request, owner_id=uuid.UUID(ctx.participant_id))
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/token", response_model=GetTokenResponse)
async def get_token(
    request: GetTokenRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> GetTokenResponse:
    """OAuth2 client_credentials grant – exchange API key for JWT tokens."""
    api_key_info = await _resolve_api_key_info(raw_request)
    try:
        return await svc.get_token(db, request, api_key_info)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.get("/participants/{participant_id}", response_model=ParticipantDetailResponse)
async def get_participant(
    participant_id: uuid.UUID,
    ctx: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> ParticipantDetailResponse:
    """Get participant details (authenticated access)."""
    try:
        return await svc.get_participant(db, participant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: uuid.UUID,
    ctx: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> AgentDetailResponse:
    """Get agent details (authenticated access)."""
    try:
        return await svc.get_agent(db, agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_agent(
    agent_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> None:
    """Terminate an agent. Requires owner role + verified MFA challenge.

    The caller must pass an ``X-MFA-Verified`` header containing a verified
    challenge ID for the ``agent_terminate`` purpose.
    """
    # MFA verification: check the X-MFA-Verified header
    mfa_header = request.headers.get("X-MFA-Verified")
    if not mfa_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA verification required for agent termination. "
            "Create a challenge via POST /mfa/verify and pass the challenge ID "
            "in the X-MFA-Verified header.",
        )

    # Validate the challenge
    challenge = await db.get(MfaChallenge, uuid.UUID(mfa_header))
    if challenge is None or challenge.status != MfaChallengeStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA challenge not verified or invalid",
        )
    if str(challenge.participant_id) != ctx.participant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA challenge does not belong to authenticated participant",
        )

    try:
        await svc.terminate_agent(
            db,
            agent_id=agent_id,
            owner_id=uuid.UUID(ctx.participant_id),
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: ApiKeyCreateRequest,
    ctx: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> ApiKeyCreateResponse:
    """Create a new API key for the authenticated participant."""
    return await svc.create_api_key(
        db,
        request,
        participant_id=uuid.UUID(ctx.participant_id),
        participant_type=ctx.participant_type,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    ctx: AuthContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> None:
    """Revoke an API key. Only owners can revoke keys."""
    try:
        await svc.revoke_api_key(
            db,
            key_id=key_id,
            revoked_by=uuid.UUID(ctx.participant_id),
            reason="revoked_by_owner",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_totp(
    ctx: AuthContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> MfaSetupResponse:
    """Initialize TOTP-based MFA for the authenticated owner."""
    try:
        return await svc.setup_totp(db, participant_id=uuid.UUID(ctx.participant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post("/mfa/verify", response_model=MfaVerifyResponse)
async def verify_mfa_challenge(
    request: MfaVerifyRequest,
    db: AsyncSession = Depends(get_db),
    svc: IdentityService = Depends(_get_service),
) -> MfaVerifyResponse:
    """Verify an MFA challenge (TOTP code, SMS code, etc.)."""
    return await svc.verify_mfa_challenge(db, request)
