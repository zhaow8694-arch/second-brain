# AIMart 工程执行文件 03：AgentCard 校验器
tags: [aimart, agent-card, validator]

tags: [aimart, agent-card, validator]
> Codex 执行指令：实现 AgentCard 的 Schema 校验、语义校验和上架验证流水线
tags: [aimart, agent-card, validator]

tags: [aimart, agent-card, validator]
---
tags: [aimart, agent-card, validator]

## 一、校验架构

```
AgentCard 提交
    │
    ▼
┌──────────────┐     失败     ┌──────────────┐
│ Schema 校验   │────────────→│ 返回校验错误  │
│ (JSON Schema) │             └──────────────┘
└──────┬───────┘
       │ 通过
       ▼
┌──────────────┐     失败     ┌──────────────┐
│ 语义校验      │────────────→│ 返回校验错误  │
│ (业务规则)    │             └──────────────┘
└──────┬───────┘
       │ 通过
       ▼
┌──────────────┐     失败     ┌──────────────┐
│ 安全扫描      │────────────→│ 返回安全报告  │
│ (技能类必选)   │             └──────────────┘
└──────┬───────┘
       │ 通过
       ▼
┌──────────────┐
│ 商品上架      │
│ (写入数据库+索引)│
└──────────────┘
```

---

## 二、Schema 校验器

```python
# src/aimart/catalog/validator.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator, ValidationError
import structlog

logger = structlog.get_logger()

# JSON Schema 文件路径
SCHEMAS_DIR = Path(__file__).parent.parent.parent.parent / "schemas"

# 商品类型 → 扩展层 Schema 映射
EXTENSION_SCHEMAS = {
    "model": "agentcard_model_v1.json",
    "skill": "agentcard_skill_v1.json",
    "expert": "agentcard_expert_v1.json",
    "compute": "agentcard_compute_v1.json",
}


class SchemaValidationError:
    """Schema 校验错误"""

    def __init__(self, path: str, message: str, schema_id: str | None = None):
        self.path = path
        self.message = message
        self.schema_id = schema_id

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "message": self.message,
            "schema_id": self.schema_id,
        }


class AgentCardSchemaValidator:
    """AgentCard JSON Schema 校验器"""

    def __init__(self) -> None:
        self._base_validator: Draft202012Validator | None = None
        self._extension_validators: dict[str, Draft202012Validator] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """加载所有 JSON Schema 文件"""
        base_schema_path = SCHEMAS_DIR / "agentcard_base_v1.json"
        if base_schema_path.exists():
            with open(base_schema_path) as f:
                base_schema = json.load(f)
            self._base_validator = Draft202012Validator(base_schema)

        for item_type, schema_file in EXTENSION_SCHEMAS.items():
            schema_path = SCHEMAS_DIR / schema_file
            if schema_path.exists():
                with open(schema_path) as f:
                    schema = json.load(f)
                self._extension_validators[item_type] = Draft202012Validator(schema)

    def validate(self, agentcard: dict[str, Any]) -> list[SchemaValidationError]:
        """校验 AgentCard：先基础层，再扩展层"""
        errors: list[SchemaValidationError] = []

        # 1. 基础层校验
        if self._base_validator:
            for error in sorted(self._base_validator.iter_errors(agentcard), key=lambda e: list(e.path)):
                errors.append(SchemaValidationError(
                    path=".".join(str(p) for p in error.path) or "root",
                    message=error.message,
                    schema_id="agentcard_base_v1",
                ))
        else:
            logger.warning("base_schema_not_loaded")

        # 2. 扩展层校验
        item_type = agentcard.get("identity", {}).get("item_type")
        if item_type and item_type in self._extension_validators:
            ext_validator = self._extension_validators[item_type]
            ext_data = agentcard.get(f"{item_type}_extension", {})
            for error in sorted(ext_validator.iter_errors(ext_data), key=lambda e: list(e.path)):
                errors.append(SchemaValidationError(
                    path=f"{item_type}_extension." + ".".join(str(p) for p in error.path),
                    message=error.message,
                    schema_id=EXTENSION_SCHEMAS[item_type],
                ))

        return errors
```

---

## 三、语义校验器

```python
# src/aimart/catalog/semantic_validator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class SemanticValidationError:
    """语义校验错误"""
    rule_id: str
    field_path: str
    message: str
    severity: str  # error | warning

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "field_path": self.field_path,
            "message": self.message,
            "severity": self.severity,
        }


class AgentCardSemanticValidator:
    """AgentCard 语义校验器——校验 Schema 无法覆盖的业务规则"""

    def validate(self, agentcard: dict[str, Any]) -> list[SemanticValidationError]:
        errors: list[SemanticValidationError] = []

        errors.extend(self._validate_identity(agentcard))
        errors.extend(self._validate_capability_declaration(agentcard))
        errors.extend(self._validate_performance_declaration(agentcard))
        errors.extend(self._validate_pricing(agentcard))
        errors.extend(self._validate_delivery(agentcard))
        errors.extend(self._validate_trust(agentcard))
        errors.extend(self._validate_legal(agentcard))

        # 按商品类型做扩展校验
        item_type = agentcard.get("identity", {}).get("item_type")
        if item_type == "skill":
            errors.extend(self._validate_skill_extension(agentcard))
        elif item_type == "expert":
            errors.extend(self._validate_expert_extension(agentcard))
        elif item_type == "compute":
            errors.extend(self._validate_compute_extension(agentcard))

        return errors

    def _validate_identity(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        identity = card.get("identity", {})

        # item_type 必须是四种之一
        valid_types = {"model", "skill", "expert", "compute"}
        if identity.get("item_type") not in valid_types:
            errors.append(SemanticValidationError(
                rule_id="SEM-ID-001",
                field_path="identity.item_type",
                message=f"item_type must be one of {valid_types}, got '{identity.get('item_type')}'",
                severity="error",
            ))

        # 版本号格式检查（semver）
        version = identity.get("item_version", "")
        if version and not self._is_semver(version):
            errors.append(SemanticValidationError(
                rule_id="SEM-ID-002",
                field_path="identity.item_version",
                message=f"Version should follow semver (e.g., 2.3.1), got '{version}'",
                severity="warning",
            ))

        return errors

    def _validate_capability_declaration(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        cap = card.get("capability_declaration", {})

        # domains 不能为空
        if not cap.get("domains"):
            errors.append(SemanticValidationError(
                rule_id="SEM-CAP-001",
                field_path="capability_declaration.domains",
                message="domains must not be empty",
                severity="error",
            ))

        # task_types 至少有一个
        if not cap.get("task_types") or len(cap.get("task_types", [])) == 0:
            errors.append(SemanticValidationError(
                rule_id="SEM-CAP-002",
                field_path="capability_declaration.task_types",
                message="At least one task_type is required",
                severity="error",
            ))

        # 每个 task_type 必须有 input_schema 和 output_schema
        for i, tt in enumerate(cap.get("task_types", [])):
            if not tt.get("input_schema"):
                errors.append(SemanticValidationError(
                    rule_id="SEM-CAP-003",
                    field_path=f"capability_declaration.task_types[{i}].input_schema",
                    message=f"Task type '{tt.get('name', i)}' must have input_schema",
                    severity="error",
                ))
            if not tt.get("output_schema"):
                errors.append(SemanticValidationError(
                    rule_id="SEM-CAP-004",
                    field_path=f"capability_declaration.task_types[{i}].output_schema",
                    message=f"Task type '{tt.get('name', i)}' must have output_schema",
                    severity="error",
                ))

        # boundary_declaration 不能为空
        boundary = cap.get("boundary_declaration", {})
        if not boundary.get("in_scope") and not boundary.get("out_of_scope"):
            errors.append(SemanticValidationError(
                rule_id="SEM-CAP-005",
                field_path="capability_declaration.boundary_declaration",
                message="At least in_scope or out_of_scope must be declared",
                severity="warning",
            ))

        return errors

    def _validate_performance_declaration(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        perf = card.get("performance_declaration", {})

        # 必须有基准测试（TR-002）
        benchmarks = perf.get("benchmarks", [])
        if not benchmarks:
            errors.append(SemanticValidationError(
                rule_id="SEM-PERF-001",
                field_path="performance_declaration.benchmarks",
                message="At least one benchmark result is required (TR-002)",
                severity="error",
            ))

        # 声明值不得超过验证值的 110%（TR-003）
        for i, b in enumerate(benchmarks):
            declared = b.get("declared_value")
            verified = b.get("verified_value")
            if declared is not None and verified is not None and verified > 0:
                ratio = declared / verified
                if ratio > 1.10:
                    errors.append(SemanticValidationError(
                        rule_id="SEM-PERF-002",
                        field_path=f"performance_declaration.benchmarks[{i}]",
                        message=f"Declared value {declared} exceeds 110% of verified {verified} (ratio: {ratio:.2f}) (TR-003)",
                        severity="error",
                    ))

        # performance_constraints 必须有 latency 和 availability
        constraints = perf.get("performance_constraints", {})
        if not constraints.get("latency_p99_ms"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PERF-003",
                field_path="performance_declaration.performance_constraints.latency_p99_ms",
                message="latency_p99_ms is required in performance_constraints",
                severity="error",
            ))
        if not constraints.get("availability_sla"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PERF-004",
                field_path="performance_declaration.performance_constraints.availability_sla",
                message="availability_sla is required in performance_constraints",
                severity="error",
            ))

        return errors

    def _validate_pricing(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        pricing = card.get("pricing", {})

        # 定价模型必须是合法值
        valid_models = {"per_call", "per_token", "per_minute", "per_hour", "subscription", "free"}
        if pricing.get("model") not in valid_models:
            errors.append(SemanticValidationError(
                rule_id="SEM-PRICE-001",
                field_path="pricing.model",
                message=f"pricing.model must be one of {valid_models}",
                severity="error",
            ))

        # 定价详情必须与 model 匹配
        model = pricing.get("model", "")
        details = pricing.get("details", {})
        if model == "per_call" and not details.get("per_call"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PRICE-002",
                field_path="pricing.details.per_call",
                message="per_call pricing requires per_call details",
                severity="error",
            ))
        elif model == "per_token" and not details.get("per_token"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PRICE-003",
                field_path="pricing.details.per_token",
                message="per_token pricing requires per_token details",
                severity="error",
            ))
        elif model == "subscription" and not details.get("subscription"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PRICE-004",
                field_path="pricing.details.subscription",
                message="subscription pricing requires subscription details",
                severity="error",
            ))

        # 免费商品也必须有 free_tier 或 details.free=True
        if model == "free" and not details.get("free_tier"):
            errors.append(SemanticValidationError(
                rule_id="SEM-PRICE-005",
                field_path="pricing.details.free_tier",
                message="free pricing should have free_tier details",
                severity="warning",
            ))

        return errors

    def _validate_delivery(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        delivery = card.get("delivery", {})

        # 交付方式必须是合法值
        valid_methods = {"api_call", "weight_download", "code_package", "instance"}
        if delivery.get("method") not in valid_methods:
            errors.append(SemanticValidationError(
                rule_id="SEM-DELIVERY-001",
                field_path="delivery.method",
                message=f"delivery.method must be one of {valid_methods}",
                severity="error",
            ))

        # api_call 必须有 endpoint
        if delivery.get("method") == "api_call" and not delivery.get("api_endpoint"):
            errors.append(SemanticValidationError(
                rule_id="SEM-DELIVERY-002",
                field_path="delivery.api_endpoint",
                message="api_call delivery requires api_endpoint",
                severity="error",
            ))

        # 支持的协议至少包含一个
        if not delivery.get("supported_protocols") or len(delivery.get("supported_protocols", [])) == 0:
            errors.append(SemanticValidationError(
                rule_id="SEM-DELIVERY-003",
                field_path="delivery.supported_protocols",
                message="At least one supported protocol is required",
                severity="error",
            ))

        return errors

    def _validate_trust(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        # 新上架商品 trust_score 由平台初始化，不在 AgentCard 中声明
        # 此处只校验结构合规
        return errors

    def _validate_legal(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        legal = card.get("legal", {})

        # data_handling.input_data_retention 必须声明
        data_handling = legal.get("data_handling", {})
        if not data_handling.get("input_data_retention"):
            errors.append(SemanticValidationError(
                rule_id="SEM-LEGAL-001",
                field_path="legal.data_handling.input_data_retention",
                message="input_data_retention must be declared",
                severity="error",
            ))

        # data_handling.input_data_usage 必须声明
        if not data_handling.get("input_data_usage"):
            errors.append(SemanticValidationError(
                rule_id="SEM-LEGAL-002",
                field_path="legal.data_handling.input_data_usage",
                message="input_data_usage must be declared",
                severity="error",
            ))

        return errors

    def _validate_skill_extension(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        ext = card.get("skill_extension", {})

        # 技能类型必须合法
        valid_types = {"tool", "workflow", "agent_template", "mcp_server"}
        if ext.get("skill_type") not in valid_types:
            errors.append(SemanticValidationError(
                rule_id="SEM-SKILL-001",
                field_path="skill_extension.skill_type",
                message=f"skill_type must be one of {valid_types}",
                severity="error",
            ))

        # 运行时环境必须声明
        runtime = ext.get("runtime", {})
        if not runtime.get("environment"):
            errors.append(SemanticValidationError(
                rule_id="SEM-SKILL-002",
                field_path="skill_extension.runtime.environment",
                message="Runtime environment is required for skills",
                severity="error",
            ))

        # 资源需求必须声明
        resources = ext.get("resource_requirements", {})
        if not resources:
            errors.append(SemanticValidationError(
                rule_id="SEM-SKILL-003",
                field_path="skill_extension.resource_requirements",
                message="Resource requirements must be declared for skills",
                severity="error",
            ))

        # 上下文数据访问必须声明
        context_access = ext.get("context_data_access", {})
        if context_access is None:
            errors.append(SemanticValidationError(
                rule_id="SEM-SKILL-004",
                field_path="skill_extension.context_data_access",
                message="context_data_access must be declared (even if requires_agent_context=false)",
                severity="error",
            ))

        return errors

    def _validate_expert_extension(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        ext = card.get("expert_extension", {})

        # 知识库更新频率必须声明
        kb = ext.get("knowledge_base", {})
        if not kb.get("update_frequency"):
            errors.append(SemanticValidationError(
                rule_id="SEM-EXPERT-001",
                field_path="expert_extension.knowledge_base.update_frequency",
                message="Knowledge base update frequency is required for experts",
                severity="error",
            ))

        # 司法管辖区必须声明
        domain = ext.get("domain", {})
        if not domain.get("jurisdictions_covered"):
            errors.append(SemanticValidationError(
                rule_id="SEM-EXPERT-002",
                field_path="expert_extension.domain.jurisdictions_covered",
                message="At least one jurisdiction must be declared",
                severity="error",
            ))

        return errors

    def _validate_compute_extension(self, card: dict) -> list[SemanticValidationError]:
        errors = []
        ext = card.get("compute_extension", {})

        # GPU 类型必须声明
        instance = ext.get("instance_type", {})
        if not instance.get("gpu_type"):
            errors.append(SemanticValidationError(
                rule_id="SEM-COMPUTE-001",
                field_path="compute_extension.instance_type.gpu_type",
                message="GPU type is required for compute items",
                severity="error",
            ))

        # 可用性 SLA 必须声明
        availability = ext.get("availability", {})
        if not availability.get("sla_uptime_pct"):
            errors.append(SemanticValidationError(
                rule_id="SEM-COMPUTE-002",
                field_path="compute_extension.availability.sla_uptime_pct",
                message="SLA uptime percentage is required for compute items",
                severity="error",
            ))

        return errors

    @staticmethod
    def _is_semver(version: str) -> bool:
        """简单 semver 格式检查"""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        try:
            int(parts[0])
            int(parts[1])
            # 第三部分可能有 -alpha 之类的后缀
            int(parts[2].split("-")[0])
            return True
        except ValueError:
            return False
```

---

## 四、校验流水线

```python
# src/aimart/catalog/validation_pipeline.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aimart.catalog.validator import AgentCardSchemaValidator, SchemaValidationError
from aimart.catalog.semantic_validator import AgentCardSemanticValidator, SemanticValidationError
import structlog

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """校验流水线整体结果"""
    valid: bool = True
    schema_errors: list[SchemaValidationError] = field(default_factory=list)
    semantic_errors: list[SemanticValidationError] = field(default_factory=list)
    security_scan_result: str = "pending"  # pending | clean | warning | failed
    security_scan_details: dict | None = None

    @property
    def all_errors(self) -> list[dict]:
        errors = [e.to_dict() for e in self.schema_errors]
        errors.extend([e.to_dict() for e in self.semantic_errors if e.severity == "error"])
        return errors

    @property
    def warnings(self) -> list[dict]:
        return [e.to_dict() for e in self.semantic_errors if e.severity == "warning"]


class AgentCardValidationPipeline:
    """AgentCard 校验流水线"""

    def __init__(self) -> None:
        self.schema_validator = AgentCardSchemaValidator()
        self.semantic_validator = AgentCardSemanticValidator()

    async def validate(self, agentcard: dict[str, Any], skip_security: bool = False) -> ValidationResult:
        """执行完整校验流水线"""

        result = ValidationResult()

        # Stage 1: Schema 校验
        logger.info("validation_pipeline_start", stage="schema")
        result.schema_errors = self.schema_validator.validate(agentcard)
        if result.schema_errors:
            result.valid = False
            logger.warning("schema_validation_failed", error_count=len(result.schema_errors))
            return result  # Schema 不过则不继续

        # Stage 2: 语义校验
        logger.info("validation_pipeline_continue", stage="semantic")
        result.semantic_errors = self.semantic_validator.validate(agentcard)
        if any(e.severity == "error" for e in result.semantic_errors):
            result.valid = False
            logger.warning("semantic_validation_failed", error_count=len(result.semantic_errors))
            return result

        # Stage 3: 安全扫描（仅技能类，且非跳过模式）
        item_type = agentcard.get("identity", {}).get("item_type")
        if item_type == "skill" and not skip_security:
            logger.info("validation_pipeline_continue", stage="security_scan")
            result.security_scan_result, result.security_scan_details = await self._run_security_scan(agentcard)
            if result.security_scan_result == "failed":
                result.valid = False
                logger.warning("security_scan_failed")
                return result

        logger.info("validation_pipeline_complete", valid=result.valid)
        return result

    async def _run_security_scan(self, agentcard: dict) -> tuple[str, dict | None]:
        """执行安全扫描（对接沙箱服务）"""
        # TODO: 对接 Sandbox Service 执行实际扫描
        # 当前返回模拟结果
        return "clean", {"scan_type": "sandbox_static_analysis", "issues_found": 0}
```

---

## 五、在 Catalog Service 中集成

```python
# src/aimart/catalog/service.py (关键方法)

from aimart.catalog.validation_pipeline import AgentCardValidationPipeline, ValidationResult
from aimart.audit.logger import audit_logger


class CatalogService:

    def __init__(self):
        self.validation_pipeline = AgentCardValidationPipeline()

    async def list_item(self, provider_id: str, agentcard: dict) -> dict:
        """上架商品"""

        # 1. 校验流水线
        result = await self.validation_pipeline.validate(agentcard)

        # 2. 记录审计日志
        await audit_logger.log(
            log_type="LOG-CT-LIST",
            actor_type="provider",
            actor_id=provider_id,
            target_type="item",
            action="list",
            result="success" if result.valid else "validation_failed",
            data={
                "item_type": agentcard.get("identity", {}).get("item_type"),
                "item_name": agentcard.get("identity", {}).get("item_name"),
                "schema_errors": len(result.schema_errors),
                "semantic_errors": len(result.semantic_errors),
                "security_scan_result": result.security_scan_result,
            },
        )

        # 3. 校验失败则返回错误
        if not result.valid:
            return {
                "status": "validation_failed",
                "errors": result.all_errors,
                "warnings": result.warnings,
            }

        # 4. 校验通过，写入数据库和搜索索引
        # ... (数据库写入和索引更新逻辑)
```

---

## 六、JSON Schema 文件生成

从 AIMart_Capability.md 中的 Schema 定义提取为独立的 JSON Schema 文件：

```json
// schemas/agentcard_base_v1.json (从能力文件提取的关键结构)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://aimart.dev/schemas/agentcard/v1.0/base",
  "title": "AgentCard Base Schema v1.0",
  "type": "object",
  "required": ["agentcard_id", "schema_version", "identity", "capability_declaration", "performance_declaration", "pricing", "delivery"],
  "properties": {
    "agentcard_id": { "type": "string", "format": "uuid" },
    "agentcard_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+" },
    "schema_version": { "type": "string", "const": "1.0" },
    "identity": {
      "type": "object",
      "required": ["provider_id", "item_id", "item_name", "item_type", "item_version"],
      "properties": {
        "provider_id": { "type": "string", "format": "uuid" },
        "provider_name": { "type": "string" },
        "item_id": { "type": "string", "format": "uuid" },
        "item_name": { "type": "string", "minLength": 1, "maxLength": 255 },
        "item_type": { "type": "string", "enum": ["model", "skill", "expert", "compute"] },
        "item_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+" },
        "item_release_date": { "type": "string", "format": "date" },
        "item_changelog_url": { "type": "string", "format": "uri" }
      }
    },
    "capability_declaration": {
      "type": "object",
      "required": ["domains", "task_types"],
      "properties": {
        "domains": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "supported_languages": { "type": "array", "items": { "type": "string" } },
        "task_types": { "type": "array", "minItems": 1 },
        "boundary_declaration": { "type": "object" }
      }
    },
    "performance_declaration": {
      "type": "object",
      "required": ["benchmarks", "performance_constraints"],
      "properties": {
        "benchmarks": { "type": "array", "minItems": 1 },
        "performance_constraints": { "type": "object" }
      }
    },
    "pricing": {
      "type": "object",
      "required": ["model", "currency"],
      "properties": {
        "model": { "type": "string", "enum": ["per_call", "per_token", "per_minute", "per_hour", "subscription", "free"] },
        "currency": { "type": "string", "enum": ["CNY", "USD", "USDC"] },
        "details": { "type": "object" },
        "bulk_discount": { "type": "array" }
      }
    },
    "delivery": {
      "type": "object",
      "required": ["method", "supported_protocols"],
      "properties": {
        "method": { "type": "string", "enum": ["api_call", "weight_download", "code_package", "instance"] },
        "api_endpoint": { "type": "string", "format": "uri" },
        "supported_protocols": { "type": "array", "items": { "type": "string", "enum": ["rest", "mcp", "a2a"] }, "minItems": 1 },
        "api_version": { "type": "string" },
        "rate_limit": { "type": "object" }
      }
    },
    "trust": { "type": "object" },
    "compatibility": { "type": "object" },
    "legal": {
      "type": "object",
      "required": ["license", "data_handling"],
      "properties": {
        "license": { "type": "string" },
        "data_handling": {
          "type": "object",
          "required": ["input_data_retention", "input_data_usage"],
          "properties": {
            "input_data_retention": { "type": "string", "enum": ["none", "30d", "90d", "indefinite"] },
            "input_data_usage": { "type": "string", "enum": ["service_only", "training_allowed", "analytics_only"] },
            "data_residency": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## 七、Codex 执行指令

```
1. 从 AIMart_Capability.md 提取完整 JSON Schema，写入 schemas/ 目录下 5 个 .json 文件
2. 实现 src/aimart/catalog/validator.py：AgentCardSchemaValidator（基于 jsonschema 库）
3. 实现 src/aimart/catalog/semantic_validator.py：AgentCardSemanticValidator（20+ 条语义规则）
4. 实现 src/aimart/catalog/validation_pipeline.py：三层流水线（Schema → 语义 → 安全扫描）
5. 在 src/aimart/catalog/service.py 的 list_item 方法中集成校验流水线
6. 编写 tests/unit/test_agentcard_validator.py：
   - 测试合法 AgentCard 通过校验
   - 测试缺少必填字段时 Schema 校验失败
   - 测试声明值超过 110% 验证值时语义校验失败
   - 测试技能类商品缺少安全扫描时校验失败
   - 测试定价模型与详情不匹配时校验失败
7. 运行 pytest tests/unit/test_agentcard_validator.py 验证
```
