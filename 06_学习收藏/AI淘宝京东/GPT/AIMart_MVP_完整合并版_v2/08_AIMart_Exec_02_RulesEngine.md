<!-- AIMart 完整合并版 v2：保留原始文件内容，并追加 Codex MVP 落地补充。生成日期：2026-06-06 -->

# AIMart 工程执行文件 02：规则引擎

> Codex 执行指令：实现基于规则的决策引擎，将 AIMart_Constraints.md 中的约束转化为可执行逻辑

---

## 一、规则引擎架构

### 1.1 核心设计

```python
# src/aimart/rules/engine.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import structlog

logger = structlog.get_logger()


class RuleSeverity(str, Enum):
    """规则违规严重级别"""
    INFO = "info"          # 记录但不阻止
    WARNING = "warning"    # 警告但不阻止
    BLOCK = "block"        # 阻止操作
    SUSPEND = "suspend"    # 暂停参与者


class RuleCategory(str, Enum):
    """规则类别"""
    TRADING = "trading"       # 交易规则（TR-xxx）
    BUDGET = "budget"         # 预算规则
    SECURITY = "security"     # 安全规则（SEC-xxx）
    SLA = "sla"              # SLA 规则
    PRICING = "pricing"       # 定价规则（PRICING-xxx）


@dataclass
class RuleContext:
    """规则评估上下文——携带所有规则可能需要的运行时数据"""
    # 操作者
    actor_type: str               # agent | owner | provider | platform
    actor_id: str
    owner_id: str | None = None

    # 操作
    operation: str                # order_create | item_list | payment_settle | ...
    target_type: str | None = None
    target_id: str | None = None

    # 商品信息（商品相关规则需要）
    item_type: str | None = None  # model | skill | expert | compute
    item_id: str | None = None
    agentcard: dict | None = None

    # 交易信息（交易相关规则需要）
    order_id: str | None = None
    amount_cny: float | None = None
    pricing_model: str | None = None

    # 预算信息（预算相关规则需要）
    budget_pool_id: str | None = None
    budget_balance: float | None = None
    budget_daily_spent: float | None = None
    budget_daily_max: float | None = None
    budget_weekly_spent: float | None = None
    budget_weekly_max: float | None = None
    budget_monthly_spent: float | None = None
    budget_monthly_max: float | None = None
    per_call_max: float | None = None
    agent_daily_spent: float | None = None
    agent_daily_max: float | None = None

    # 效果回传（信任相关规则需要）
    effect_score: int | None = None
    success: bool | None = None
    actual_latency_ms: int | None = None
    declared_latency_ms: int | None = None
    declaration_accuracy: float | None = None

    # 授权信息
    spending_authority_level: str | None = None  # L0 | L1 | L2 | L3

    # 安全信息
    security_scan_result: str | None = None  # clean | warning | failed
    sandbox_verified: bool | None = None
    data_sensitivity: str | None = None      # public | internal | confidential | restricted


@dataclass
class RuleResult:
    """单条规则的评估结果"""
    rule_id: str
    rule_name: str
    category: RuleCategory
    passed: bool
    severity: RuleSeverity
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleEvaluationResult:
    """规则引擎整体评估结果"""
    results: list[RuleResult] = field(default_factory=list)
    blocked: bool = False
    blocked_by: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    audit_events: list[dict] = field(default_factory=list)

    def add(self, result: RuleResult) -> None:
        self.results.append(result)
        if not result.passed:
            if result.severity == RuleSeverity.BLOCK:
                self.blocked = True
                self.blocked_by.append(result.rule_id)
            elif result.severity == RuleSeverity.SUSPEND:
                self.blocked = True
                self.blocked_by.append(result.rule_id)
            elif result.severity == RuleSeverity.WARNING:
                self.warnings.append(f"{result.rule_id}: {result.message}")


class Rule:
    """单条规则的抽象基类"""

    rule_id: str = ""
    rule_name: str = ""
    category: RuleCategory = RuleCategory.TRADING
    severity: RuleSeverity = RuleSeverity.BLOCK
    applies_to_operations: list[str] = []  # 空列表 = 适用于所有操作

    def applies(self, context: RuleContext) -> bool:
        """判断此规则是否适用于当前上下文"""
        if not self.applies_to_operations:
            return True
        return context.operation in self.applies_to_operations

    async def evaluate(self, context: RuleContext) -> RuleResult:
        """评估规则，子类必须实现"""
        raise NotImplementedError


class RulesEngine:
    """规则引擎——加载所有规则，按上下文评估，返回结果"""

    def __init__(self) -> None:
        self._rules: list[Rule] = []
        self._logger = structlog.get_logger()

    def register(self, rule: Rule) -> None:
        self._rules.append(rule)
        self._logger.info("rule_registered", rule_id=rule.rule_id, rule_name=rule.rule_name)

    async def evaluate(self, context: RuleContext) -> RuleEvaluationResult:
        """评估所有适用规则"""
        result = RuleEvaluationResult()

        for rule in self._rules:
            if not rule.applies(context):
                continue

            try:
                rule_result = await rule.evaluate(context)
                result.add(rule_result)

                if not rule_result.passed:
                    self._logger.warning(
                        "rule_violation",
                        rule_id=rule.rule_id,
                        actor_id=context.actor_id,
                        operation=context.operation,
                        message=rule_result.message,
                    )
            except Exception as e:
                self._logger.error(
                    "rule_evaluation_error",
                    rule_id=rule.rule_id,
                    error=str(e),
                )
                # 规则评估出错时保守处理：阻止操作
                result.add(RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    category=rule.category,
                    passed=False,
                    severity=RuleSeverity.BLOCK,
                    message=f"Rule evaluation error: {str(e)}",
                ))

        return result
```

---

## 二、交易规则实现

```python
# src/aimart/rules/trading_rules.py

from aimart.rules.engine import Rule, RuleContext, RuleResult, RuleCategory, RuleSeverity


class TR001_AgentCardRequired(Rule):
    """TR-001: 上架商品必须提供 AgentCard"""
    rule_id = "TR-001"
    rule_name = "agentcard_required"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["item_list"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        has_card = context.agentcard is not None and len(context.agentcard) > 0
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=has_card,
            severity=self.severity,
            message="AgentCard is required for listing" if not has_card else "",
        )


class TR002_BenchmarkRequired(Rule):
    """TR-002: 上架商品必须提供至少一项基准测试结果"""
    rule_id = "TR-002"
    rule_name = "benchmark_required"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["item_list"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.agentcard is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, False, self.severity, "No AgentCard provided")

        benchmarks = context.agentcard.get("performance_declaration", {}).get("benchmarks", [])
        has_benchmark = len(benchmarks) > 0
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=has_benchmark,
            severity=self.severity,
            message="At least one benchmark result is required" if not has_benchmark else "",
        )


class TR003_DeclarationOverpromise(Rule):
    """TR-003: 能力声明不得高于基准测试结果的 110%"""
    rule_id = "TR-003"
    rule_name = "declaration_overpromise_check"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["item_list"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.agentcard is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, False, self.severity, "No AgentCard")

        benchmarks = context.agentcard.get("performance_declaration", {}).get("benchmarks", [])
        violations = []
        for b in benchmarks:
            declared = b.get("declared_value")
            verified = b.get("verified_value")
            if declared is not None and verified is not None and verified > 0:
                ratio = declared / verified
                if ratio > 1.10:
                    violations.append({
                        "benchmark": b.get("benchmark_name"),
                        "metric": b.get("metric"),
                        "declared": declared,
                        "verified": verified,
                        "ratio": round(ratio, 3),
                    })

        passed = len(violations) == 0
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Performance declaration exceeds 110% of verified value for {len(violations)} metrics" if violations else "",
            data={"violations": violations},
        )


class TR006_SkillSecurityScan(Rule):
    """TR-006: 技能类商品必须通过沙箱安全扫描"""
    rule_id = "TR-006"
    rule_name = "skill_security_scan"
    category = RuleCategory.SECURITY
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["item_list"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.item_type != "skill":
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        scan_result = context.security_scan_result
        sandbox_ok = context.sandbox_verified

        passed = scan_result == "clean" and sandbox_ok is True
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Skill security scan result: {scan_result}, sandbox verified: {sandbox_ok}" if not passed else "",
        )


class TR017_OrderExpiry(Rule):
    """TR-017: 订单创建后 30 秒内未完成支付自动过期（此规则在订单创建时标记，由定时任务执行）"""
    rule_id = "TR-017"
    rule_name = "order_expiry_check"
    category = RuleCategory.TRADING
    severity = RuleSeverity.WARNING
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        # 此规则在订单创建时仅做标记，过期由后台任务处理
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Order will expire in 30 seconds if not paid",
            data={"expiry_seconds": 30},
        )


class TR020_EffectReportWindow(Rule):
    """TR-020: 效果回传窗口期为交付后 24 小时"""
    rule_id = "TR-020"
    rule_name = "effect_report_window"
    category = RuleCategory.TRADING
    severity = RuleSeverity.WARNING
    applies_to_operations = ["effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        # 窗口期检查在 service 层执行，此规则仅做提醒
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Effect report must be submitted within 24 hours of delivery",
            data={"window_hours": 24},
        )
```

---

## 三、预算规则实现

```python
# src/aimart/rules/budget_rules.py

from aimart.rules.engine import Rule, RuleContext, RuleResult, RuleCategory, RuleSeverity


class BUDGET001_InsufficientBalance(Rule):
    """预算池余额不足时拒绝交易"""
    rule_id = "BUDGET-001"
    rule_name = "insufficient_balance"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.amount_cny is None or context.budget_balance is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        passed = context.budget_balance >= context.amount_cny
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Insufficient balance: {context.budget_balance} < {context.amount_cny}" if not passed else "",
            data={"balance": context.budget_balance, "required": context.amount_cny},
        )


class BUDGET002_DailyLimitExceeded(Rule):
    """日消费限额检查"""
    rule_id = "BUDGET-002"
    rule_name = "daily_limit_exceeded"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.amount_cny is None or context.budget_daily_spent is None or context.budget_daily_max is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        projected = context.budget_daily_spent + context.amount_cny
        passed = projected <= context.budget_daily_max
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Daily limit would be exceeded: {projected} > {context.budget_daily_max}" if not passed else "",
            data={"daily_spent": context.budget_daily_spent, "amount": context.amount_cny, "daily_max": context.budget_daily_max},
        )


class BUDGET003_WeeklyLimitExceeded(Rule):
    """周消费限额检查"""
    rule_id = "BUDGET-003"
    rule_name = "weekly_limit_exceeded"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.amount_cny is None or context.budget_weekly_spent is None or context.budget_weekly_max is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        projected = context.budget_weekly_spent + context.amount_cny
        passed = projected <= context.budget_weekly_max
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Weekly limit would be exceeded: {projected} > {context.budget_weekly_max}" if not passed else "",
        )


class BUDGET004_MonthlyLimitExceeded(Rule):
    """月消费限额检查"""
    rule_id = "BUDGET-004"
    rule_name = "monthly_limit_exceeded"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.amount_cny is None or context.budget_monthly_spent is None or context.budget_monthly_max is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        projected = context.budget_monthly_spent + context.amount_cny
        passed = projected <= context.budget_monthly_max
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Monthly limit would be exceeded: {projected} > {context.budget_monthly_max}" if not passed else "",
        )


class BUDGET005_AgentDailyLimit(Rule):
    """Agent 日消费限额检查"""
    rule_id = "BUDGET-005"
    rule_name = "agent_daily_limit"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.actor_type != "agent":
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")
        if context.amount_cny is None or context.agent_daily_spent is None or context.agent_daily_max is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        projected = context.agent_daily_spent + context.amount_cny
        passed = projected <= context.agent_daily_max
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=f"Agent daily limit would be exceeded: {projected} > {context.agent_daily_max}" if not passed else "",
        )


class BUDGET006_SpendingAuthorityLevel(Rule):
    """分层授权检查：根据金额判断需要的授权级别"""
    rule_id = "BUDGET-006"
    rule_name = "spending_authority_level"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    LEVELS = [
        (0.01, "L0", "全自动"),
        (1.00, "L1", "事后通知"),
        (100.00, "L2", "事前审批"),
        (float("inf"), "L3", "人工确认"),
    ]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.amount_cny is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        # 判断此金额需要的授权级别
        required_level = "L3"
        required_desc = "人工确认"
        for threshold, level, desc in self.LEVELS:
            if context.amount_cny <= threshold:
                required_level = level
                required_desc = desc
                break

        # 检查 Agent 当前授权级别是否足够
        current_level = context.spending_authority_level or "L0"
        level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
        passed = level_order.get(current_level, 0) >= level_order.get(required_level, 3)

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity if not passed else RuleSeverity.INFO,
            message=f"Authorization level {required_level} ({required_desc}) required for amount {context.amount_cny} CNY" if not passed else f"Authorization level {required_level} sufficient",
            data={
                "required_level": required_level,
                "current_level": current_level,
                "amount": context.amount_cny,
                "description": required_desc,
            },
        )
```

---

## 四、安全规则实现

```python
# src/aimart/rules/security_rules.py

from aimart.rules.engine import Rule, RuleContext, RuleResult, RuleCategory, RuleSeverity


class SEC008_DataSensitivityTransfer(Rule):
    """SEC-008: 传递给技能的上下文数据敏感度检查"""
    rule_id = "SEC-008"
    rule_name = "data_sensitivity_transfer_check"
    category = RuleCategory.SECURITY
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create", "delivery"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.item_type != "skill":
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        # 检查技能声明的最大敏感度 vs 实际传递的敏感度
        if context.agentcard is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        skill_ext = context.agentcard.get("skill_extension", {})
        max_allowed = skill_ext.get("context_data_access", {}).get("data_sensitivity_max", "public")

        sensitivity_order = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
        actual = context.data_sensitivity or "public"

        passed = sensitivity_order.get(actual, 0) <= sensitivity_order.get(max_allowed, 0)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity if not passed else RuleSeverity.INFO,
            message=f"Data sensitivity {actual} exceeds skill's max allowed {max_allowed}" if not passed else "",
            data={"actual_sensitivity": actual, "max_allowed": max_allowed},
        )


class SEC014_EffectReportNoRawInput(Rule):
    """SEC-014: 效果回传数据不得包含原始输入内容"""
    rule_id = "SEC-014"
    rule_name = "effect_report_no_raw_input"
    category = RuleCategory.SECURITY
    severity = RuleSeverity.WARNING
    applies_to_operations = ["effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        # 此规则在 service 层做数据脱敏后检查，此处仅做标记
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Effect report must not contain raw input content - enforced at service layer",
        )
```

---

## 五、SLA 规则实现

```python
# src/aimart/rules/sla_rules.py

from aimart.rules.engine import Rule, RuleContext, RuleResult, RuleCategory, RuleSeverity


class SLA001_LatencyViolation(Rule):
    """SLA 延迟违约自动检测"""
    rule_id = "SLA-001"
    rule_name = "latency_violation"
    category = RuleCategory.SLA
    severity = RuleSeverity.WARNING
    applies_to_operations = ["effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.actual_latency_ms is None or context.declared_latency_ms is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        violated = context.actual_latency_ms > context.declared_latency_ms * 2  # 超过声明值 200%
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=not violated,
            severity=self.severity,
            message=f"Latency violation: actual {context.actual_latency_ms}ms > 2x declared {context.declared_latency_ms}ms" if violated else "",
            data={"actual_ms": context.actual_latency_ms, "declared_ms": context.declared_latency_ms},
        )


class SLA002_DeclarationAccuracy(Rule):
    """声明准确性检查——效果回传偏差超过 20% 触发调查"""
    rule_id = "SLA-002"
    rule_name = "declaration_accuracy"
    category = RuleCategory.SLA
    severity = RuleSeverity.WARNING
    applies_to_operations = ["effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        if context.declaration_accuracy is None:
            return RuleResult(self.rule_id, self.rule_name, self.category, True, self.severity, "")

        violated = context.declaration_accuracy < 0.80  # 低于 80%
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=not violated,
            severity=self.severity,
            message=f"Declaration accuracy below threshold: {context.declaration_accuracy:.0%}" if violated else "",
            data={"accuracy": context.declaration_accuracy, "threshold": 0.80},
        )
```

---

## 六、规则注册表

```python
# src/aimart/rules/registry.py

from aimart.rules.engine import RulesEngine
from aimart.rules.trading_rules import (
    TR001_AgentCardRequired,
    TR002_BenchmarkRequired,
    TR003_DeclarationOverpromise,
    TR006_SkillSecurityScan,
    TR017_OrderExpiry,
    TR020_EffectReportWindow,
)
from aimart.rules.budget_rules import (
    BUDGET001_InsufficientBalance,
    BUDGET002_DailyLimitExceeded,
    BUDGET003_WeeklyLimitExceeded,
    BUDGET004_MonthlyLimitExceeded,
    BUDGET005_AgentDailyLimit,
    BUDGET006_SpendingAuthorityLevel,
)
from aimart.rules.security_rules import (
    SEC008_DataSensitivityTransfer,
    SEC014_EffectReportNoRawInput,
)
from aimart.rules.sla_rules import (
    SLA001_LatencyViolation,
    SLA002_DeclarationAccuracy,
)


def create_rules_engine() -> RulesEngine:
    """创建并注册所有规则的规则引擎实例"""
    engine = RulesEngine()

    # 交易规则
    engine.register(TR001_AgentCardRequired())
    engine.register(TR002_BenchmarkRequired())
    engine.register(TR003_DeclarationOverpromise())
    engine.register(TR006_SkillSecurityScan())
    engine.register(TR017_OrderExpiry())
    engine.register(TR020_EffectReportWindow())

    # 预算规则
    engine.register(BUDGET001_InsufficientBalance())
    engine.register(BUDGET002_DailyLimitExceeded())
    engine.register(BUDGET003_WeeklyLimitExceeded())
    engine.register(BUDGET004_MonthlyLimitExceeded())
    engine.register(BUDGET005_AgentDailyLimit())
    engine.register(BUDGET006_SpendingAuthorityLevel())

    # 安全规则
    engine.register(SEC008_DataSensitivityTransfer())
    engine.register(SEC014_EffectReportNoRawInput())

    # SLA 规则
    engine.register(SLA001_LatencyViolation())
    engine.register(SLA002_DeclarationAccuracy())

    return engine


# 全局单例
rules_engine = create_rules_engine()
```

---

## 七、在 Service 层集成规则引擎

```python
# src/aimart/exchange/service.py (骨架示例)

from aimart.rules.registry import rules_engine
from aimart.rules.engine import RuleContext, RuleCategory
from aimart.audit.logger import audit_logger


class ExchangeService:

    async def create_order(self, agent_id: str, item_id: str, amount: float, **kwargs) -> dict:
        """创建订单——集成规则引擎评估"""

        # 1. 构建规则上下文
        context = RuleContext(
            actor_type="agent",
            actor_id=agent_id,
            operation="order_create",
            item_id=item_id,
            amount_cny=amount,
            # ... 从数据库加载预算信息填充上下文
        )

        # 2. 规则引擎评估
        result = await rules_engine.evaluate(context)

        # 3. 记录审计日志
        await audit_logger.log(
            log_type="LOG-EX-ORDER-CREATE",
            actor_type="agent",
            actor_id=agent_id,
            target_type="order",
            action="create",
            result="blocked" if result.blocked else "success",
            data={
                "item_id": item_id,
                "amount_cny": amount,
                "rules_evaluated": len(result.results),
                "rules_blocked_by": result.blocked_by,
                "rules_warnings": result.warnings,
            },
        )

        # 4. 根据结果决定是否继续
        if result.blocked:
            raise RuleViolationError(
                blocked_by=result.blocked_by,
                warnings=result.warnings,
            )

        # 5. 继续订单创建逻辑
        # ...
```

---

## 八、Codex 执行指令

```
1. 创建 src/aimart/rules/ 目录下的所有文件
2. 实现 engine.py：RuleContext、RuleResult、RuleEvaluationResult、Rule、RulesEngine
3. 实现 trading_rules.py：TR-001 至 TR-024（优先实现 TR-001/002/003/006/017/020）
4. 实现 budget_rules.py：BUDGET-001 至 BUDGET-006（全部实现）
5. 实现 security_rules.py：SEC-008、SEC-014（其余 SEC 规则在沙箱模块中实现）
6. 实现 sla_rules.py：SLA-001、SLA-002
7. 实现 registry.py：注册所有规则，创建全局 rules_engine 单例
8. 编写 tests/unit/test_rules_engine.py：覆盖所有规则的通过/失败场景
9. 在 exchange/service.py 中集成规则引擎调用
10. 在 catalog/service.py 中集成商品上架规则（TR-001/002/003/006）
11. 在 payment/service.py 中集成预算规则（BUDGET-001~006）
```

---

# v2.0 Codex 执行补充：规则引擎决策顺序与标准错误码

## 1. 规则检查顺序

任何 Agent 执行能力前，必须按以下顺序检查：

```text
1. actor_identity_check
2. role_permission_check
3. agent_owner_binding_check
4. agent_maturity_check
5. capability_status_check
6. seller_status_check
7. risk_level_check
8. budget_check
9. data_policy_check
10. compliance_region_check
11. payment_mode_check
12. audit_required_check
```

## 2. 标准错误码

```text
PERMISSION_DENIED
AGENT_OWNER_REQUIRED
AGENT_MATURITY_REQUIRED
CAPABILITY_NOT_ACTIVE
SELLER_SUSPENDED
HIGH_RISK_REQUIRES_HUMAN_APPROVAL
BUDGET_EXCEEDED
DATA_POLICY_REQUIRES_APPROVAL
CROSS_BORDER_DATA_BLOCKED
COMPUTE_DERIVATIVE_BLOCKED
REAL_PAYMENT_DISABLED_IN_MVP
AUDIT_REQUIRED
```

## 3. Decision 对象

所有规则检查必须返回：

```json
{
  "allowed": false,
  "decision_code": "AGENT_MATURITY_REQUIRED",
  "reason": "Agent maturity level M0 is below required M2",
  "required_approval": false,
  "audit_required": true
}
```

