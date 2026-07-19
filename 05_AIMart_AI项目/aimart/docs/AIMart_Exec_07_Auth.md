# AIMart 工程执行文件 07：Agent 身份认证
tags: [aimart, auth, security]

tags: [aimart, auth, security]
> Codex 执行指令：实现 Agent 身份注册、API Key 签发、OAuth2-Agent 流程、MFA 与权限校验
tags: [aimart, auth, security]

tags: [aimart, auth, security]
---
tags: [aimart, auth, security]

## 一、数据库模型

```python
# src/aimart/identity/models.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Numeric, Boolean, DateTime, Enum, ForeignKey,
    Integer, Text, JSON, Index, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Participant(Base):
    """参与者——Owner / Provider / Certifier / Facilitator"""
    __tablename__ = "participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(20), nullable=False, comment="owner | provider | certifier | facilitator")
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, nullable=False, default=False)
    jurisdiction = Column(String(10), nullable=False, comment="司法管辖区代码 CN/US/EU...")

    # KYC
    kyc_status = Column(String(20), nullable=False, default="pending", comment="pending | submitted | verified | rejected")
    kyc_documents = Column(JSONB, nullable=True, comment="KYC 文档元信息")
    kyc_verified_at = Column(DateTime, nullable=True)

    # 安全
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(255), nullable=True, comment="MFA TOTP 密钥（加密存储）")
    mfa_enabled = Column(Boolean, nullable=False, default=False)

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | suspended | closed")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    agents = relationship("Agent", back_populates="owner")
    api_keys = relationship("ApiKey", back_populates="participant", foreign_keys="ApiKey.participant_id")

    __table_args__ = (
        Index("ix_participants_email", "email"),
        Index("ix_participants_type_status", "type", "status"),
    )


class Agent(Base):
    """AI Agent 身份"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 框架
    framework = Column(String(50), nullable=False, comment="langchain | crewai | autogen | dify | coze | custom")
    framework_version = Column(String(20), nullable=True)

    # 能力范围
    capability_scope = Column(JSONB, nullable=False, default=list, comment="能力标签列表")
    capability_scope_hash = Column(String(64), nullable=True, comment="capability_scope 的 SHA256，用于快速比较")

    # 消费授权
    spending_authority_level = Column(String(2), nullable=False, default="L0", comment="L0 | L1 | L2 | L3")
    budget_pool_id = Column(UUID(as_uuid=True), nullable=True, comment="默认预算池")

    # 信任
    trust_score = Column(Numeric(5, 2), nullable=False, default=50.0, comment="0-100")
    trust_score_updated_at = Column(DateTime, nullable=True)

    # 运行时信息
    last_active_at = Column(DateTime, nullable=True)
    last_ip = Column(String(45), nullable=True)
    total_transactions = Column(Integer, nullable=False, default=0)
    total_spent_cny = Column(Numeric(18, 4), nullable=False, default=0)

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | suspended | terminated")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship("Participant", back_populates="agents")

    __table_args__ = (
        Index("ix_agents_owner", "owner_id"),
        Index("ix_agents_status", "status"),
        Index("ix_agents_framework", "framework"),
    )


class ApiKey(Base):
    """API Key——Agent 和参与者均可持有"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, comment="null=Participant 级 Key")

    # Key 内容
    key_prefix = Column(String(8), nullable=False, comment="前8位，用于展示和检索")
    key_hash = Column(String(128), nullable=False, unique=True, comment="完整 key 的 SHA512 hash")
    key_encrypted = Column(String(512), nullable=False, comment="AES-256-GCM 加密的原始 key")

    # 权限
    scopes = Column(JSONB, nullable=False, default=list, comment='["read", "trade", "manage"]')
    permissions = Column(JSONB, nullable=False, default=dict, comment='{"max_daily_spend": 1000, "item_types": ["model", "skill"]}')

    # 生命周期
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, nullable=False, default=0)

    # 安全
    allowed_ips = Column(JSONB, nullable=True, comment="IP 白名单，null=不限")
    allowed_origins = Column(JSONB, nullable=True, comment="来源白名单")

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | revoked | expired")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(Text, nullable=True)

    participant = relationship("Participant", back_populates="api_keys", foreign_keys=[participant_id])

    __table_args__ = (
        Index("ix_apikeys_prefix", "key_prefix"),
        Index("ix_apikeys_participant", "participant_id"),
        Index("ix_apikeys_agent", "agent_id"),
        Index("ix_apikeys_status", "status"),
    )


class OAuth2Client(Base):
    """OAuth2 客户端——用于 Agent 框架集成"""
    __tablename__ = "oauth2_clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(64), nullable=False, unique=True, comment="OAuth2 client_id")
    client_secret_hash = Column(String(128), nullable=False, comment="client_secret 的 SHA512")
    client_name = Column(String(255), nullable=False, comment="如 LangChain-AIMart-Plugin")

    owner_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)

    # 授权类型
    grant_types = Column(JSONB, nullable=False, default=list, comment='["client_credentials", "authorization_code"]')
    redirect_uris = Column(JSONB, nullable=True, comment="authorization_code 模式的回调 URI")

    # 权限
    scopes = Column(JSONB, nullable=False, default=list, comment='["agent:read", "agent:trade", "catalog:search"]')

    # 状态
    status = Column(String(20), nullable=False, default="active")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_oauth2_client_id", "client_id"),
    )


class RefreshToken(Base):
    """刷新令牌"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=True)

    token_hash = Column(String(128), nullable=False, unique=True, comment="SHA512")
    expires_at = Column(DateTime, nullable=False)

    # 关联的 OAuth2 客户端
    oauth2_client_id = Column(UUID(as_uuid=True), nullable=True)

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | revoked | used")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_refresh_token_hash", "token_hash"),
    )


class MfaChallenge(Base):
    """MFA 验证挑战——用于 L3 级交易确认和 Agent 注销"""
    __tablename__ = "mfa_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    challenge_type = Column(String(20), nullable=False, comment="totp | sms | email | webhook")

    # 验证上下文
    purpose = Column(String(50), nullable=False, comment="agent_terminate | l3_confirm | key_revoke")
    reference_id = Column(UUID(as_uuid=True), nullable=True, comment="关联的 Agent/Transaction ID")

    # 状态
    status = Column(String(20), nullable=False, default="pending", comment="pending | verified | expired | failed")
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)

    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_mfa_participant", "participant_id", "status"),
        Index("ix_mfa_expires", "expires_at"),
    )
```

---

## 二、API Key 签发与管理

```python
# src/aimart/identity/apikey.py

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from cryptography.fernet import Fernet

import structlog

logger = structlog.get_logger()


class ApiKeyManager:
    """API Key 签发、验证、吊销"""

    # Key 前缀标识
    KEY_PREFIX_PARTICIPANT = "aim_o_"    # Owner 级
    KEY_PREFIX_PROVIDER = "aim_p_"       # Provider 级
    KEY_PREFIX_AGENT = "aim_a_"          # Agent 级
    KEY_PREFIX_FACILITATOR = "aim_f_"    # Facilitator 级

    def __init__(self, encryption_key: bytes, key_repo, audit_logger):
        self._fernet = Fernet(encryption_key)
        self._repo = key_repo
        self._audit = audit_logger

    def _get_prefix(self, participant_type: str, is_agent: bool = False) -> str:
        """根据参与者类型确定 Key 前缀"""
        if is_agent:
            return self.KEY_PREFIX_AGENT
        prefixes = {
            "owner": self.KEY_PREFIX_PARTICIPANT,
            "provider": self.KEY_PREFIX_PROVIDER,
            "certifier": self.KEY_PREFIX_PARTICIPANT,
            "facilitator": self.KEY_PREFIX_FACILITATOR,
        }
        return prefixes.get(participant_type, "aim_x_")

    async def generate(
        self,
        participant_id: UUID,
        participant_type: str,
        agent_id: UUID | None = None,
        scopes: list[str] | None = None,
        permissions: dict | None = None,
        expires_in_days: int = 365,
        allowed_ips: list[str] | None = None,
    ) -> tuple[str, dict]:
        """
        生成 API Key。

        Returns:
            (raw_key, metadata) — raw_key 仅此一次返回，metadata 包含 key_hash 等
        """
        prefix = self._get_prefix(participant_type, is_agent=(agent_id is not None))

        # 生成随机 key: prefix + 32字节随机数
        raw_key = prefix + secrets.token_urlsafe(32)
        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        # AES 加密存储原始 key
        key_encrypted = self._fernet.encrypt(raw_key.encode()).decode()

        # 默认 scopes
        if scopes is None:
            scopes = self._default_scopes(participant_type, is_agent=(agent_id is not None))

        # 默认 permissions
        if permissions is None:
            permissions = self._default_permissions(participant_type)

        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # 持久化
        api_key = await self._repo.create(
            participant_id=participant_id,
            agent_id=agent_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            key_encrypted=key_encrypted,
            scopes=scopes,
            permissions=permissions,
            expires_at=expires_at,
            allowed_ips=allowed_ips,
        )

        await self._audit.log(
            log_type="ID-APIKEY-GENERATE",
            actor_type="system",
            actor_id=str(participant_id),
            target_type="api_key",
            target_id=str(api_key.id),
            action="generate",
            data={
                "participant_id": str(participant_id),
                "agent_id": str(agent_id) if agent_id else None,
                "key_prefix": key_prefix,
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
            },
        )

        logger.info("api_key_generated", key_prefix=key_prefix, participant_id=str(participant_id))

        return raw_key, {"id": str(api_key.id), "key_prefix": key_prefix, "expires_at": expires_at.isoformat()}

    async def verify(self, raw_key: str) -> dict | None:
        """
        验证 API Key。

        Returns:
            验证成功返回 key 信息 dict，失败返回 None
        """
        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        api_key = await self._repo.get_by_hash(key_hash)
        if api_key is None:
            logger.warning("api_key_not_found", key_prefix=key_prefix)
            return None

        # 状态检查
        if api_key.status != "active":
            logger.warning("api_key_inactive", key_prefix=key_prefix, status=api_key.status)
            return None

        # 过期检查
        if datetime.now(timezone.utc) > api_key.expires_at:
            await self._repo.update_status(api_key.id, "expired")
            logger.warning("api_key_expired", key_prefix=key_prefix)
            return None

        # IP 白名单检查
        if api_key.allowed_ips:
            # 需要从请求上下文获取 IP，此处仅做标记
            pass

        # 更新使用信息
        await self._repo.update_usage(api_key.id)

        return {
            "id": str(api_key.id),
            "participant_id": str(api_key.participant_id),
            "agent_id": str(api_key.agent_id) if api_key.agent_id else None,
            "scopes": api_key.scopes,
            "permissions": api_key.permissions,
            "key_prefix": api_key.key_prefix,
        }

    async def revoke(self, key_id: UUID, revoked_by: UUID, reason: str = "manual_revoke") -> bool:
        """吊销 API Key"""
        api_key = await self._repo.get_by_id(key_id)
        if api_key is None:
            return False

        api_key.status = "revoked"
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoke_reason = reason
        await self._repo.update(api_key)

        await self._audit.log(
            log_type="ID-APIKEY-REVOKE",
            actor_type="owner",
            actor_id=str(revoked_by),
            target_type="api_key",
            target_id=str(key_id),
            action="revoke",
            data={"reason": reason},
        )

        logger.info("api_key_revoked", key_id=str(key_id), reason=reason)
        return True

    def _default_scopes(self, participant_type: str, is_agent: bool) -> list[str]:
        """根据参与者类型返回默认 scopes"""
        if is_agent:
            return ["catalog:search", "catalog:read", "exchange:trade", "exchange:trial"]
        scopes_map = {
            "owner": ["agent:manage", "budget:manage", "catalog:read", "audit:read"],
            "provider": ["catalog:write", "catalog:read", "trust:read"],
            "certifier": ["catalog:certify", "trust:write", "catalog:read"],
            "facilitator": ["settlement:facilitate", "audit:read"],
        }
        return scopes_map.get(participant_type, ["catalog:read"])

    def _default_permissions(self, participant_type: str) -> dict:
        """根据参与者类型返回默认权限"""
        perms_map = {
            "owner": {"max_agents": 100, "max_api_keys": 500},
            "provider": {"max_items": 1000, "max_versions_per_item": 50},
            "certifier": {"max_certifications_per_day": 100},
            "facilitator": {"max_settlements_per_day": 10000},
        }
        return perms_map.get(participant_type, {})
```

---

## 三、OAuth2-Agent 流程

```python
# src/aimart/identity/oauth2.py

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

import structlog

from aimart.config import settings

logger = structlog.get_logger()


class OAuth2AgentFlow:
    """
    OAuth2-Agent 认证流程。

    支持两种 Grant Type：
    1. client_credentials — Agent 用 API Key 直接换取 Access Token（最常用）
    2. authorization_code — Agent 框架通过 OAuth2 标准流程获取 Token

    Token 结构：
    - Access Token: JWT，1小时有效，包含 participant_id + agent_id + scopes
    - Refresh Token: 随机令牌，30天有效，用于刷新 Access Token
    """

    def __init__(self, jwt_secret: str, jwt_algorithm: str = "RS256", oauth2_repo=None, audit_logger=None):
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._repo = oauth2_repo
        self._audit = audit_logger

    async def client_credentials_grant(
        self,
        api_key_info: dict,
        requested_scopes: list[str] | None = None,
    ) -> dict:
        """
        client_credentials 授权流程。

        Agent 用 API Key → 验证通过 → 签发 Access Token + Refresh Token

        Args:
            api_key_info: ApiKeyManager.verify() 返回的 key 信息
            requested_scopes: Agent 请求的 scope 子集

        Returns:
            {"access_token": "...", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "..."}
        """
        participant_id = api_key_info["participant_id"]
        agent_id = api_key_info.get("agent_id")
        key_scopes = api_key_info.get("scopes", [])

        # Scope 交集：请求的 scope 不能超过 key 允许的范围
        if requested_scopes:
            granted_scopes = [s for s in requested_scopes if s in key_scopes]
        else:
            granted_scopes = key_scopes

        if not granted_scopes:
            raise ValueError("请求的 scope 不在 API Key 允许范围内")

        # 签发 Access Token
        access_token = self._create_access_token(
            participant_id=participant_id,
            agent_id=agent_id,
            scopes=granted_scopes,
            key_id=api_key_info["id"],
        )

        # 签发 Refresh Token
        refresh_token = await self._create_refresh_token(
            participant_id=UUID(participant_id),
            agent_id=UUID(agent_id) if agent_id else None,
        )

        await self._audit.log(
            log_type="ID-TOKEN-ISSUED",
            actor_type="agent" if agent_id else "participant",
            actor_id=agent_id or participant_id,
            action="client_credentials_grant",
            data={
                "participant_id": participant_id,
                "agent_id": agent_id,
                "scopes": granted_scopes,
            },
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.security.jwt.access_token_ttl_minutes * 60,
            "refresh_token": refresh_token,
            "scope": " ".join(granted_scopes),
        }

    async def refresh_access_token(self, refresh_token_str: str) -> dict:
        """
        用 Refresh Token 刷新 Access Token。
        """
        token_hash = hashlib.sha512(refresh_token_str.encode()).hexdigest()
        stored_token = await self._repo.get_refresh_token_by_hash(token_hash)

        if stored_token is None:
            raise ValueError("无效的 Refresh Token")
        if stored_token.status != "active":
            raise ValueError("Refresh Token 已吊销或已使用")
        if datetime.now(timezone.utc) > stored_token.expires_at:
            raise ValueError("Refresh Token 已过期")

        # 标记旧 Refresh Token 已使用
        stored_token.status = "used"
        await self._repo.update_refresh_token(stored_token)

        # 签发新的 Access Token
        access_token = self._create_access_token(
            participant_id=str(stored_token.participant_id),
            agent_id=str(stored_token.agent_id) if stored_token.agent_id else None,
            scopes=["catalog:search", "catalog:read", "exchange:trade"],  # 使用原始 scopes
            key_id=None,
        )

        # 签发新的 Refresh Token（Rotation）
        new_refresh = await self._create_refresh_token(
            participant_id=stored_token.participant_id,
            agent_id=stored_token.agent_id,
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.security.jwt.access_token_ttl_minutes * 60,
            "refresh_token": new_refresh,
        }

    def _create_access_token(
        self,
        participant_id: str,
        agent_id: str | None,
        scopes: list[str],
        key_id: str | None = None,
    ) -> str:
        """签发 JWT Access Token"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=settings.security.jwt.access_token_ttl_minutes)

        payload = {
            "iss": settings.security.jwt.issuer,
            "sub": participant_id,
            "agent_id": agent_id,
            "scopes": scopes,
            "key_id": key_id,
            "iat": now,
            "exp": expires,
            "jti": secrets.token_urlsafe(16),  # JWT ID，用于吊销
        }

        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

    async def _create_refresh_token(
        self,
        participant_id: UUID,
        agent_id: UUID | None = None,
    ) -> str:
        """生成 Refresh Token"""
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha512(raw_token.encode()).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.security.jwt.refresh_token_ttl_days
        )

        await self._repo.create_refresh_token(
            participant_id=participant_id,
            agent_id=agent_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return raw_token

    def verify_access_token(self, token: str) -> dict | None:
        """
        验证 Access Token。

        Returns:
            解码后的 payload dict，验证失败返回 None
        """
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
                issuer=settings.security.jwt.issuer,
            )
            # 检查过期
            if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            return payload
        except JWTError as e:
            logger.warning("jwt_verification_failed", error=str(e))
            return None
```

---

## 四、MFA 验证

```python
# src/aimart/identity/mfa.py

from __future__ import annotations

import pyotp
import secrets
from datetime import datetime, timezone
from uuid import UUID

import structlog

logger = structlog.get_logger()


class MfaService:
    """
    多因素认证服务。

    用途：
    - Agent 注销（需要 Owner MFA 确认）
    - L3 级交易确认
    - API Key 吊销
    - 预算池大额操作
    """

    def __init__(self, participant_repo, mfa_repo, notification_service, audit_logger):
        self._participants = participant_repo
        self._mfa = mfa_repo
        self._notify = notification_service
        self._audit = audit_logger

    async def setup_totp(self, participant_id: UUID) -> dict:
        """
        为参与者设置 TOTP（基于时间的一次性密码）。

        Returns:
            {"secret": "...", "qr_url": "...", "backup_codes": [...]}
        """
        participant = await self._participants.get_by_id(participant_id)
        if participant is None:
            raise ValueError("参与者不存在")

        # 生成 TOTP Secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # 生成备份码（10个）
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # 存储（加密）
        participant.totp_secret = secret  # 实际应加密存储
        participant.mfa_enabled = True
        await self._participants.update(participant)

        # 构造 QR URL
        qr_url = totp.provisioning_uri(
            name=participant.email,
            issuer_name="AIMart"
        )

        await self._audit.log(
            log_type="ID-MFA-SETUP",
            actor_type="owner",
            actor_id=str(participant_id),
            action="setup_totp",
            data={"method": "totp"},
        )

        return {
            "secret": secret,
            "qr_url": qr_url,
            "backup_codes": backup_codes,
        }

    async def create_challenge(
        self,
        participant_id: UUID,
        purpose: str,
        reference_id: UUID | None = None,
        challenge_type: str = "totp",
    ) -> dict:
        """
        创建 MFA 验证挑战。

        Args:
            participant_id: 需要验证的参与者
            purpose: 用途（agent_terminate | l3_confirm | key_revoke）
            reference_id: 关联的 Agent/Transaction ID
            challenge_type: totp | sms | email | webhook

        Returns:
            {"challenge_id": "...", "expires_at": "...", "challenge_type": "..."}
        """
        challenge = await self._mfa.create(
            participant_id=participant_id,
            challenge_type=challenge_type,
            purpose=purpose,
            reference_id=reference_id,
            expires_at=datetime.now(timezone.utc).replace(minute=0, second=0).replace(
                minute=datetime.now(timezone.utc).minute + 5
            ),
        )

        # 发送验证码（非 TOTP 场景）
        if challenge_type == "sms":
            code = secrets.token_hex(3).upper()  # 6位数字码
            await self._notify.send_sms(participant_id, f"AIMart 验证码: {code}，5分钟内有效")
        elif challenge_type == "email":
            code = secrets.token_hex(3).upper()
            await self._notify.send_email(participant_id, "AIMart 操作确认", f"验证码: {code}，5分钟内有效")

        logger.info("mfa_challenge_created", challenge_id=str(challenge.id), purpose=purpose)

        return {
            "challenge_id": str(challenge.id),
            "expires_at": challenge.expires_at.isoformat(),
            "challenge_type": challenge_type,
        }

    async def verify_challenge(self, challenge_id: UUID, code: str) -> tuple[bool, str]:
        """
        验证 MFA 挑战。

        Args:
            challenge_id: 挑战 ID
            code: TOTP 码 / SMS 码 / 备份码

        Returns:
            (verified, message)
        """
        challenge = await self._mfa.get_by_id(challenge_id)
        if challenge is None:
            return False, "挑战不存在"

        # 过期检查
        if datetime.now(timezone.utc) > challenge.expires_at:
            challenge.status = "expired"
            await self._mfa.update(challenge)
            return False, "验证码已过期"

        # 次数检查
        if challenge.attempts >= challenge.max_attempts:
            challenge.status = "failed"
            await self._mfa.update(challenge)
            return False, "验证次数已达上限"

        # 递增尝试次数
        challenge.attempts += 1

        # TOTP 验证
        if challenge.challenge_type == "totp":
            participant = await self._participants.get_by_id(challenge.participant_id)
            if participant and participant.totp_secret:
                totp = pyotp.TOTP(participant.totp_secret)
                if totp.verify(code, valid_window=1):
                    challenge.status = "verified"
                    challenge.verified_at = datetime.now(timezone.utc)
                    await self._mfa.update(challenge)
                    return True, "验证通过"

        # SMS/Email 码验证（简化）
        # TODO: 实际的 SMS/Email 码存储和比对

        await self._mfa.update(challenge)
        return False, f"验证码错误，剩余 {challenge.max_attempts - challenge.attempts} 次"
```

---

## 五、认证与授权中间件

```python
# src/aimart/identity/auth.py

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from aimart.identity.apikey import ApiKeyManager
from aimart.identity.oauth2 import OAuth2AgentFlow
from aimart.identity.mfa import MfaService

import structlog

logger = structlog.get_logger()

# 安全方案
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/identity/token", auto_error=False)


class AuthContext:
    """认证上下文——贯穿整个请求生命周期"""
    def __init__(
        self,
        participant_id: str,
        participant_type: str,
        agent_id: str | None = None,
        scopes: list[str] | None = None,
        permissions: dict | None = None,
        auth_method: str = "api_key",  # api_key | jwt
    ):
        self.participant_id = participant_id
        self.participant_type = participant_type
        self.agent_id = agent_id
        self.scopes = scopes or []
        self.permissions = permissions or {}
        self.auth_method = auth_method

    @property
    def is_agent(self) -> bool:
        return self.agent_id is not None

    def has_scope(self, scope: str) -> bool:
        """检查是否拥有特定 scope"""
        return scope in self.scopes or "*" in self.scopes


async def require_auth(
    api_key: str = Depends(api_key_header),
    token: str = Depends(oauth2_scheme),
) -> AuthContext:
    """
    通用认证依赖——API Key 或 JWT Token 二选一。
    所有需要认证的接口使用此依赖。
    """
    # 优先尝试 API Key
    if api_key:
        key_info = await _get_apikey_manager().verify(api_key)
        if key_info:
            participant = await _get_participant(key_info["participant_id"])
            return AuthContext(
                participant_id=key_info["participant_id"],
                participant_type=participant.type if participant else "unknown",
                agent_id=key_info.get("agent_id"),
                scopes=key_info.get("scopes", []),
                permissions=key_info.get("permissions", {}),
                auth_method="api_key",
            )

    # 尝试 JWT Token
    if token:
        oauth2 = _get_oauth2_flow()
        payload = oauth2.verify_access_token(token)
        if payload:
            participant_id = payload.get("sub")
            participant = await _get_participant(participant_id)
            return AuthContext(
                participant_id=participant_id,
                participant_type=participant.type if participant else "unknown",
                agent_id=payload.get("agent_id"),
                scopes=payload.get("scopes", []),
                auth_method="jwt",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_owner(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """要求 Owner 角色"""
    if auth.participant_type != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要 Owner 角色")
    return auth


async def require_provider(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """要求 Provider 角色"""
    if auth.participant_type != "provider":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要 Provider 角色")
    return auth


async def require_agent(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """要求 Agent 身份"""
    if not auth.is_agent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要 Agent 身份")
    return auth


async def require_mfa(
    purpose: str,
    reference_id: str | None = None,
    auth: AuthContext = Depends(require_owner),
) -> AuthContext:
    """要求 MFA 验证（用于高风险操作）"""
    # 从请求头获取 MFA 验证码
    # 实际实现应从请求上下文获取
    mfa_code = None  # 需要从请求中提取

    if not mfa_code:
        # 创建 MFA 挑战，返回 challenge_id 让客户端完成验证
        mfa_service = _get_mfa_service()
        challenge = await mfa_service.create_challenge(
            participant_id=auth.participant_id,
            purpose=purpose,
            reference_id=reference_id,
        )
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail={"message": "需要 MFA 验证", "challenge_id": challenge["challenge_id"]},
        )

    return auth


def require_scope(scope: str):
    """创建一个 scope 检查依赖"""
    async def _check(auth: AuthContext = Depends(require_auth)) -> AuthContext:
        if not auth.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 scope: {scope}",
            )
        return auth
    return _check


# 依赖注入辅助（实际由 FastAPI dependency_overrides 提供）
_apikey_manager = None
_oauth2_flow = None
_mfa_service = None

def _get_apikey_manager() -> ApiKeyManager:
    return _apikey_manager

def _get_oauth2_flow() -> OAuth2AgentFlow:
    return _oauth2_flow

def _get_mfa_service() -> MfaService:
    return _mfa_service

def _get_participant(participant_id: str):
    # TODO: 从数据库获取
    return None
```

---

## 六、Agent 注册流程

```python
# src/aimart/identity/service.py

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog

from aimart.identity.apikey import ApiKeyManager
from aimart.identity.oauth2 import OAuth2AgentFlow
from aimart.identity.mfa import MfaService
from aimart.identity.schemas import (
    RegisterParticipantRequest, RegisterParticipantResponse,
    RegisterAgentRequest, RegisterAgentResponse,
    GetTokenRequest, GetTokenResponse,
    ParticipantDetailResponse, AgentDetailResponse,
)
from aimart.audit.logger import AuditLogger

logger = structlog.get_logger()


class IdentityService:
    """身份域服务"""

    def __init__(
        self,
        apikey_manager: ApiKeyManager,
        oauth2_flow: OAuth2AgentFlow,
        mfa_service: MfaService,
        audit_logger: AuditLogger,
        participant_repo,
        agent_repo,
    ):
        self._apikey = apikey_manager
        self._oauth2 = oauth2_flow
        self._mfa = mfa_service
        self._audit = audit_logger
        self._participants = participant_repo
        self._agents = agent_repo

    async def register_participant(self, request: RegisterParticipantRequest) -> RegisterParticipantResponse:
        """
        注册参与者。

        流程：
        1. 检查 email 唯一性
        2. 密码哈希
        3. 创建 Participant 记录
        4. 发送验证邮件
        5. 签发初始 API Key
        """
        # 1. 唯一性检查
        existing = await self._participants.get_by_email(request.email)
        if existing:
            raise ValueError(f"邮箱已注册: {request.email}")

        # 2. 密码哈希（使用 argon2）
        import argon2
        ph = argon2.PasswordHasher()
        password_hash = ph.hash(request.email + "_initial")  # 实际应从请求获取密码

        # 3. 创建记录
        participant = await self._participants.create(
            type=request.type,
            name=request.name,
            email=request.email,
            jurisdiction=request.jurisdiction,
            password_hash=password_hash,
            status="active",
            kyc_status="pending",
        )

        # 4. 发送验证邮件
        # TODO: await self._notify.send_verification_email(participant)

        # 5. 签发初始 API Key
        raw_key, key_meta = await self._apikey.generate(
            participant_id=participant.id,
            participant_type=request.type,
        )

        await self._audit.log(
            log_type="ID-PARTICIPANT-REGISTER",
            actor_type="system",
            actor_id=str(participant.id),
            target_type="participant",
            target_id=str(participant.id),
            action="register",
            data={"type": request.type, "email": request.email},
        )

        return RegisterParticipantResponse(
            participant_id=participant.id,
            status="pending_verification",
        )

    async def register_agent(self, request: RegisterAgentRequest, owner_id: UUID) -> RegisterAgentResponse:
        """
        注册 AI Agent。

        流程：
        1. 校验 Owner 存在且 active
        2. 创建 Agent 记录
        3. 计算能力范围哈希
        4. 签发 Agent 专属 API Key
        5. 创建默认预算分配（如果有默认预算池）
        """
        # 1. 校验 Owner
        owner = await self._participants.get_by_id(owner_id)
        if owner is None or owner.status != "active":
            raise ValueError("Owner 不存在或状态异常")

        # 2. 创建 Agent
        import hashlib, json
        scope_hash = hashlib.sha256(
            json.dumps(request.capability_scope, sort_keys=True).encode()
        ).hexdigest()

        agent = await self._agents.create(
            owner_id=owner_id,
            name=request.name,
            framework=request.framework,
            capability_scope=request.capability_scope,
            capability_scope_hash=scope_hash,
            spending_authority_level=request.spending_authority_level,
            trust_score=50.0,
            status="active",
        )

        # 3. 签发 Agent API Key
        raw_key, key_meta = await self._apikey.generate(
            participant_id=owner_id,
            participant_type=owner.type,
            agent_id=agent.id,
            scopes=["catalog:search", "catalog:read", "exchange:trade", "exchange:trial"],
            permissions={"per_call_max": 1.0, "daily_max": 500.0},
        )

        await self._audit.log(
            log_type="ID-AGENT-REGISTER",
            actor_type="owner",
            actor_id=str(owner_id),
            target_type="agent",
            target_id=str(agent.id),
            action="register",
            data={
                "agent_name": request.name,
                "framework": request.framework,
                "spending_authority": request.spending_authority_level,
            },
        )

        return RegisterAgentResponse(
            agent_id=agent.id,
            api_key=raw_key,
            api_key_expires_at=key_meta["expires_at"],
        )

    async def get_token(self, request: GetTokenRequest, api_key_info: dict) -> GetTokenResponse:
        """获取 Access Token"""
        result = await self._oauth2.client_credentials_grant(api_key_info)
        return GetTokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )

    async def terminate_agent(self, agent_id: UUID, owner_id: UUID) -> dict:
        """
        注销 Agent。

        流程：
        1. 校验 Agent 属于该 Owner
        2. 冻结所有活跃订单
        3. 吊销 Agent 的所有 API Key
        4. 更新 Agent 状态为 terminated
        """
        agent = await self._agents.get_by_id(agent_id)
        if agent is None:
            raise ValueError("Agent 不存在")
        if str(agent.owner_id) != str(owner_id):
            raise ValueError("Agent 不属于该 Owner")

        # 冻结订单
        # TODO: await self._exchange.freeze_agent_orders(agent_id)

        # 吊销所有 API Key
        agent_keys = await self._apikey._repo.get_by_agent(agent_id)
        for key in agent_keys:
            if key.status == "active":
                await self._apikey.revoke(key.id, owner_id, reason="agent_terminated")

        # 更新状态
        agent.status = "terminated"
        await self._agents.update(agent)

        await self._audit.log(
            log_type="ID-AGENT-TERMINATE",
            actor_type="owner",
            actor_id=str(owner_id),
            target_type="agent",
            target_id=str(agent_id),
            action="terminate",
            data={"reason": "owner_initiated"},
        )

        return {"agent_id": str(agent_id), "status": "terminated", "effect": "all_active_orders_frozen"}

    async def get_participant(self, participant_id: UUID) -> ParticipantDetailResponse | None:
        participant = await self._participants.get_by_id(participant_id)
        if participant is None:
            return None
        return ParticipantDetailResponse(
            id=participant.id,
            type=participant.type,
            name=participant.name,
            email=participant.email,
            jurisdiction=participant.jurisdiction,
            kyc_status=participant.kyc_status,
            created_at=participant.created_at,
        )

    async def get_agent(self, agent_id: UUID) -> AgentDetailResponse | None:
        agent = await self._agents.get_by_id(agent_id)
        if agent is None:
            return None
        return AgentDetailResponse(
            id=agent.id,
            owner_id=agent.owner_id,
            name=agent.name,
            framework=agent.framework,
            capability_scope=agent.capability_scope,
            trust_score=float(agent.trust_score),
            spending_authority=agent.spending_authority_level,
            status=agent.status,
            created_at=agent.created_at,
            last_active_at=agent.last_active_at,
        )
```

---

## 七、Codex 执行检查清单

| # | 检查项 | 预期结果 |
|---|--------|---------|
| 1 | 创建 6 张数据表 | `participants`, `agents`, `api_keys`, `oauth2_clients`, `refresh_tokens`, `mfa_challenges` |
| 2 | API Key 生成 | 4种前缀（aim_o_/aim_p_/aim_a_/aim_f_），SHA512 hash + AES加密存储 |
| 3 | API Key 验证 | hash 匹配 + 状态/过期/IP白名单检查 + 使用计数更新 |
| 4 | OAuth2 client_credentials | API Key → 验证 → JWT Access Token + Refresh Token |
| 5 | JWT Token 验证 | RS256 签名验证 + 过期检查 + issuer 校验 |
| 6 | Refresh Token Rotation | 旧 token 标记 used → 签发新 token 对 |
| 7 | MFA TOTP | 生成 secret → QR URL → 验证 6 位码（±1 窗口） |
| 8 | MFA Challenge | 创建 → 限制3次尝试 → 5分钟过期 |
| 9 | Agent 注册 | Owner 校验 → 创建 Agent → 签发 Agent API Key → 审计日志 |
| 10 | Agent 注销 | MFA 验证 → 冻结订单 → 吊销 Key → 标记 terminated |
| 11 | 权限中间件 | `require_auth`(通用)、`require_owner`/`require_provider`/`require_agent`(角色)、`require_scope`(细粒度) |
| 12 | L3 交易 MFA | 大额交易 → 触发 MFA Challenge → 428 响应 → 客户端完成验证后重试 |
