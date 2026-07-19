# AIMart 工程执行文件 04：审计日志系统
tags: [aimart, audit-log]

tags: [aimart, audit-log]
> Codex 执行指令：实现不可篡改的审计日志写入、哈希链校验和查询 API
tags: [aimart, audit-log]

tags: [aimart, audit-log]
---
tags: [aimart, audit-log]

## 一、审计日志写入器

```python
# src/aimart/audit/logger.py

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog

logger = structlog.get_logger()


class AuditLogger:
    """审计日志写入器——所有域的操作都通过此写入器记录日志"""

    def __init__(self, clickhouse_client, kafka_producer) -> None:
        self._ch = clickhouse_client
        self._kafka = kafka_producer
        self._last_hash: dict[str, str] = {}  # 按日志类别维护最后一条的 hash

    async def log(
        self,
        log_type: str,
        actor_type: str,
        actor_id: str,
        target_type: str | None = None,
        target_id: str | None = None,
        action: str = "",
        result: str = "success",
        error_code: str | None = None,
        error_message: str | None = None,
        data: dict[str, Any] | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> str:
        """
        写入一条审计日志。

        返回：log_id
        """

        # 1. 生成日志条目
        log_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        category = log_type.split("-")[1] if "-" in log_type else "SY"

        # 2. 计算数据 hash
        data_str = json.dumps(data or {}, sort_keys=True, ensure_ascii=False)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # 3. 获取前一条日志的 hash（构建哈希链）
        previous_hash = self._last_hash.get(category, "0" * 64)

        # 4. 计算当前条目的 hash
        hash_payload = f"{log_id}|{timestamp}|{actor_id}|{action}|{data_hash}|{previous_hash}"
        current_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

        # 5. 更新 last_hash
        self._last_hash[category] = current_hash

        # 6. 构建完整日志条目
        entry = {
            "log_id": log_id,
            "log_type": log_type,
            "timestamp": timestamp,
            "trace_id": trace_id or str(uuid4()),
            "span_id": str(uuid4()),
            "previous_hash": previous_hash,
            "current_hash": current_hash,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "session_id": session_id,
            "action_operation": action,
            "action_target_type": target_type,
            "action_target_id": target_id,
            "action_result": result,
            "action_error_code": error_code,
            "action_error_message": error_message,
            "data_hash": data_hash,
            "data": data_str,
            "context_ip_hash": hashlib.sha256(ip_address.encode()).hexdigest() if ip_address else None,
        }

        # 7. 异步写入 Kafka（用于实时消费）和 ClickHouse（用于持久化查询）
        await self._write_to_kafka(entry)
        await self._write_to_clickhouse(entry)

        logger.debug(
            "audit_log_written",
            log_id=log_id,
            log_type=log_type,
            actor_id=actor_id,
            action=action,
            result=result,
        )

        return log_id

    async def _write_to_kafka(self, entry: dict) -> None:
        """写入 Kafka 供实时消费"""
        try:
            topic = f"aimart.audit_{entry['log_type'].split('-')[1].lower() if '-' in entry['log_type'] else 'sy'}"
            await self._kafka.produce(
                topic=topic,
                key=entry["log_id"],
                value=json.dumps(entry, ensure_ascii=False).encode(),
            )
        except Exception as e:
            logger.error("audit_kafka_write_failed", error=str(e), log_id=entry.get("log_id"))

    async def _write_to_clickhouse(self, entry: dict) -> None:
        """写入 ClickHouse 供持久化查询"""
        try:
            await self._ch.execute(
                """
                INSERT INTO aimart_audit.audit_log (
                    log_id, log_type, timestamp, trace_id, span_id,
                    previous_hash, current_hash,
                    actor_type, actor_id, session_id,
                    action_operation, action_target_type, action_target_id,
                    action_result, action_error_code, action_error_message,
                    data_hash, data, context_ip_hash
                ) VALUES
                """,
                [(
                    entry["log_id"],
                    entry["log_type"],
                    entry["timestamp"],
                    entry["trace_id"],
                    entry["span_id"],
                    entry["previous_hash"],
                    entry["current_hash"],
                    entry["actor_type"],
                    entry["actor_id"],
                    entry["session_id"],
                    entry["action_operation"],
                    entry["action_target_type"],
                    entry["action_target_id"],
                    entry["action_result"],
                    entry["action_error_code"],
                    entry["action_error_message"],
                    entry["data_hash"],
                    entry["data"],
                    entry["context_ip_hash"],
                )],
            )
        except Exception as e:
            logger.error("audit_clickhouse_write_failed", error=str(e), log_id=entry.get("log_id"))
```

---

## 二、哈希链校验

```python
# src/aimart/audit/hashchain.py

from __future__ import annotations

import hashlib
import json
from typing import Any

import structlog

logger = structlog.get_logger()


class HashChainVerifier:
    """审计日志哈希链校验器"""

    @staticmethod
    def compute_hash(entry: dict[str, Any]) -> str:
        """计算单条日志条目的 hash"""
        payload = (
            f"{entry['log_id']}"
            f"|{entry['timestamp']}"
            f"|{entry['actor_id']}"
            f"|{entry['action_operation']}"
            f"|{entry['data_hash']}"
            f"|{entry['previous_hash']}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def verify_chain(cls, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """
        验证日志链完整性。

        返回：
        {
            "verified": bool,
            "total_checked": int,
            "broken_at": str | None,  # 断裂处的 log_id
            "broken_at_index": int | None,
        }
        """
        if not entries:
            return {"verified": True, "total_checked": 0, "broken_at": None, "broken_at_index": None}

        # 按 timestamp 排序
        sorted_entries = sorted(entries, key=lambda e: e["timestamp"])

        broken_at = None
        broken_at_index = None

        for i in range(1, len(sorted_entries)):
            prev = sorted_entries[i - 1]
            curr = sorted_entries[i]

            # 计算 prev 的 hash
            expected_hash = cls.compute_hash(prev)

            # 检查 curr 的 previous_hash 是否等于 prev 的计算 hash
            if curr["previous_hash"] != expected_hash:
                broken_at = curr["log_id"]
                broken_at_index = i
                logger.warning(
                    "hash_chain_broken",
                    at_log_id=curr["log_id"],
                    expected_previous_hash=expected_hash,
                    actual_previous_hash=curr["previous_hash"],
                )
                break

        verified = broken_at is None
        return {
            "verified": verified,
            "total_checked": len(sorted_entries),
            "broken_at": broken_at,
            "broken_at_index": broken_at_index,
        }

    @classmethod
    def verify_single(cls, entry: dict[str, Any], previous_entry: dict[str, Any] | None) -> bool:
        """验证单条日志与前一条的链接"""
        if previous_entry is None:
            return True  # 链首无前驱

        expected_hash = cls.compute_hash(previous_entry)
        return entry["previous_hash"] == expected_hash


class CheckpointGenerator:
    """哈希链检查点生成器——每 N 条日志生成一个检查点"""

    CHECKPOINT_INTERVAL = 10000

    @classmethod
    def generate(cls, entries: list[dict[str, Any]], date: str) -> dict[str, Any]:
        """生成一个检查点"""
        if not entries:
            return {
                "date": date,
                "entry_count": 0,
                "first_log_id": None,
                "last_log_id": None,
                "merkle_root": hashlib.sha256(b"empty").hexdigest(),
            }

        sorted_entries = sorted(entries, key=lambda e: e["timestamp"])

        # 计算 Merkle Root
        merkle_root = cls._compute_merkle_root([e["current_hash"] for e in sorted_entries])

        return {
            "date": date,
            "entry_count": len(sorted_entries),
            "first_log_id": sorted_entries[0]["log_id"],
            "last_log_id": sorted_entries[-1]["log_id"],
            "first_timestamp": sorted_entries[0]["timestamp"],
            "last_timestamp": sorted_entries[-1]["timestamp"],
            "merkle_root": merkle_root,
        }

    @staticmethod
    def _compute_merkle_root(hashes: list[str]) -> str:
        """计算 Merkle Root"""
        if not hashes:
            return hashlib.sha256(b"empty").hexdigest()

        if len(hashes) == 1:
            return hashes[0]

        # 成对哈希
        next_level = []
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                combined = hashlib.sha256(f"{hashes[i]}|{hashes[i+1]}".encode()).hexdigest()
            else:
                combined = hashes[i]
            next_level.append(combined)

        return CheckpointGenerator._compute_merkle_root(next_level)
```

---

## 三、ClickHouse 表结构

```sql
-- ClickHouse 建表语句

CREATE DATABASE IF NOT EXISTS aimart_audit;

CREATE TABLE IF NOT EXISTS aimart_audit.audit_log
(
    log_id              String,
    log_type            String,
    timestamp           DateTime64(3, 'UTC'),
    trace_id            String,
    span_id             String,
    previous_hash       String,
    current_hash        String,
    actor_type          LowCardinality(String),
    actor_id            String,
    session_id          Nullable(String),
    action_operation    String,
    action_target_type  Nullable(String),
    action_target_id    Nullable(String),
    action_result       LowCardinality(String),
    action_error_code   Nullable(String),
    action_error_message Nullable(String),
    data_hash           String,
    data                String,         -- JSON string
    context_ip_hash     Nullable(String)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (log_type, timestamp, log_id)
TTL timestamp + INTERVAL 5 YEAR
SETTINGS index_granularity = 8192;

-- 按日期的物化视图（加速日期范围查询）
CREATE MATERIALIZED VIEW IF NOT EXISTS aimart_audit.audit_log_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, log_type)
AS
SELECT
    toDate(timestamp) AS date,
    log_type,
    count() AS entry_count,
    any(log_id) AS first_log_id,
    anyLast(log_id) AS last_log_id
FROM aimart_audit.audit_log
GROUP BY date, log_type;

-- 检查点表
CREATE TABLE IF NOT EXISTS aimart_audit.checkpoints
(
    date            Date,
    category        LowCardinality(String),
    entry_count     UInt64,
    first_log_id    String,
    last_log_id     String,
    first_timestamp DateTime64(3, 'UTC'),
    last_timestamp  DateTime64(3, 'UTC'),
    merkle_root     String,
    previous_checkpoint_hash String,
    created_at      DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree()
ORDER BY (date, category)
TTL date + INTERVAL 5 YEAR;
```

---

## 四、审计查询 API

```python
# src/aimart/audit/router.py

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from aimart.audit.schemas import (
    AuditQueryRequest,
    AuditQueryResponse,
    AuditTraceResponse,
    AuditVerifyResponse,
    CheckpointResponse,
)
from aimart.identity.auth import require_auth, require_platform_or_regulator

router = APIRouter()


@router.post("/query", response_model=AuditQueryResponse)
async def query_audit_logs(
    request: AuditQueryRequest,
    auth=Depends(require_auth),
):
    """
    查询审计日志。
    权限控制：
    - Owner: 只能查所属 Agent 的日志
    - Agent: 只能查自身的日志
    - Provider: 只能查自身商品的日志
    - Platform: 全部
    - Regulator: 全部（需合规令状）
    """
    # 权限过滤逻辑在 service 层实现
    # ...


@router.get("/trace/{trace_id}", response_model=AuditTraceResponse)
async def get_audit_trace(
    trace_id: UUID,
    auth=Depends(require_auth),
):
    """按 trace_id 查询完整交易链路"""
    # ...


@router.get("/checkpoint/{checkpoint_date}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_date: date,
    auth=Depends(require_platform_or_regulator),
):
    """获取指定日期的哈希链检查点"""
    # ...


@router.post("/verify", response_model=AuditVerifyResponse)
async def verify_chain_integrity(
    date_from: date = Query(...),
    date_to: date = Query(...),
    auth=Depends(require_platform_or_regulator),
):
    """验证指定日期范围的日志链完整性"""
    # ...
```

---

## 五、审计 Pydantic Schema

```python
# src/aimart/audit/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditQueryRequest(BaseModel):
    filters: AuditQueryFilters
    pagination: AuditPagination = Field(default_factory=lambda: AuditPagination(offset=0, limit=50))
    sort: AuditSort = Field(default_factory=lambda: AuditSort(field="timestamp", order="desc"))


class AuditQueryFilters(BaseModel):
    log_types: list[str] | None = None
    actor_id: UUID | None = None
    target_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    result: str | None = None  # success | failure


class AuditPagination(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class AuditSort(BaseModel):
    field: str = "timestamp"
    order: str = "desc"  # asc | desc


class AuditLogEntryResponse(BaseModel):
    log_id: UUID
    log_type: str
    timestamp: datetime
    trace_id: UUID
    actor_type: str
    actor_id: UUID
    action_operation: str
    action_target_type: str | None
    action_target_id: UUID | None
    action_result: str
    action_error_code: str | None
    data: dict[str, Any]
    current_hash: str


class AuditQueryResponse(BaseModel):
    entries: list[AuditLogEntryResponse]
    total_count: int
    chain_integrity_verified: bool


class AuditTraceEvent(BaseModel):
    event: str
    timestamp: datetime
    log_id: UUID
    log_type: str
    actor_type: str
    action_result: str
    data: dict[str, Any]


class AuditTraceResponse(BaseModel):
    trace_id: UUID
    entries: list[AuditLogEntryResponse]
    timeline: list[AuditTraceEvent]


class CheckpointResponse(BaseModel):
    date: str
    category: str
    entry_count: int
    first_log_id: UUID
    last_log_id: UUID
    first_timestamp: datetime
    last_timestamp: datetime
    merkle_root: str


class AuditVerifyResponse(BaseModel):
    verified: bool
    total_entries_checked: int
    broken_at_log_id: UUID | None
    broken_at_timestamp: datetime | None
```

---

## 六、全局审计日志实例

```python
# src/aimart/dependencies.py (补充)

from aimart.audit.logger import AuditLogger

# 全局单例（在 lifespan 中初始化）
audit_logger: AuditLogger | None = None


async def init_clickhouse():
    global audit_logger
    # ... 初始化 ClickHouse 客户端和 Kafka Producer
    # audit_logger = AuditLogger(ch_client, kafka_producer)
```

---

## 七、在业务代码中使用审计日志

```python
# 使用示例：交易域

from aimart.dependencies import audit_logger

class ExchangeService:
    async def create_order(self, ...):
        # ... 业务逻辑 ...

        # 写入审计日志
        log_id = await audit_logger.log(
            log_type="LOG-EX-ORDER-CREATE",
            actor_type="agent",
            actor_id=agent_id,
            target_type="order",
            target_id=order_id,
            action="order_create",
            result="success",
            data={
                "item_id": item_id,
                "amount_cny": amount,
                "authorization_level_required": required_level,
            },
            trace_id=trace_id,
        )
```

---

## 八、Codex 执行指令

```
1. 在 ClickHouse 中执行建表 SQL（审计日志表 + 检查点表 + 物化视图）
2. 实现 src/aimart/audit/logger.py：AuditLogger（Kafka 双写 + ClickHouse 持久化）
3. 实现 src/aimart/audit/hashchain.py：HashChainVerifier + CheckpointGenerator
4. 实现 src/aimart/audit/schemas.py：所有 Pydantic 请求/响应模型
5. 实现 src/aimart/audit/router.py：4 个查询 API 端点
6. 实现 src/aimart/audit/service.py：查询逻辑 + 权限过滤 + 链验证调用
7. 在 src/aimart/dependencies.py 中初始化全局 audit_logger 单例
8. 编写 tests/unit/test_audit_hashchain.py：
   - 测试单条日志 hash 计算
   - 测试正常链的验证通过
   - 测试篡改链的验证失败（broken_at 正确标识）
   - 测试 Merkle Root 计算
   - 测试检查点生成
9. 编写 tests/integration/test_audit_trace.py：
   - 测试完整交易链路追踪（搜索→试用→下单→支付→交付→回传）
10. 在所有 service 层的关键操作中集成 audit_logger.log() 调用
```
