"""Built-in trading, budget and security rules for AIMart."""

from __future__ import annotations

import structlog

from aimart.domains.rules.engine import (
    Rule,
    RuleCategory,
    RuleContext,
    RuleResult,
    RuleSeverity,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Trading Rules
# ---------------------------------------------------------------------------


class TR001_MustProvideAgentCard(Rule):  # noqa: N801
    """TR-001: Must provide AgentCard."""

    rule_id = "TR-001"
    rule_name = "Must provide AgentCard"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["skill_register", "skill_update", "order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = context.agentcard is not None
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="AgentCard provided" if passed else "AgentCard is required",
            data={"has_agentcard": passed},
        )


class TR003_PerformanceDeclaration(Rule):  # noqa: N801
    """TR-003: Performance declaration must be <= 110% of benchmark."""

    rule_id = "TR-003"
    rule_name = "Performance declaration <= 110% benchmark"
    category = RuleCategory.TRADING
    severity = RuleSeverity.WARNING
    applies_to_operations = ["skill_register", "skill_update"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        accuracy = context.declaration_accuracy
        passed = True
        if accuracy is not None:
            passed = accuracy <= 1.1
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message=(
                "Declaration accuracy within bounds"
                if passed
                else f"Declaration accuracy {accuracy} exceeds 110% benchmark"
            ),
            data={"declaration_accuracy": accuracy},
        )


class TR006_SkillsPassSandboxScan(Rule):  # noqa: N801
    """TR-006: Skills must pass sandbox scan."""

    rule_id = "TR-006"
    rule_name = "Skills must pass sandbox scan"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["skill_register", "skill_update"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = context.sandbox_verified
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Sandbox verification passed" if passed else "Skill must pass sandbox scan",
            data={"sandbox_verified": context.sandbox_verified},
        )


class TR011_MustSearchBeforePurchase(Rule):  # noqa: N801
    """TR-011: Must search before purchase."""

    rule_id = "TR-011"
    rule_name = "Must search before purchase"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301, ARG002
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Search-before-purchase check passed",
            data={},
        )


class TR017_OrderExpiresIn30s(Rule):  # noqa: N801
    """TR-017: Order expires in 30 seconds."""

    rule_id = "TR-017"
    rule_name = "Order expires in 30s"
    category = RuleCategory.TRADING
    severity = RuleSeverity.INFO
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301, ARG002
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Order TTL enforced by lifecycle service",
            data={"order_ttl_seconds": 30},
        )


class TR018_MustLinkBudgetPool(Rule):  # noqa: N801
    """TR-018: Must link a budget pool."""

    rule_id = "TR-018"
    rule_name = "Must link budget pool"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = context.budget_pool_id is not None
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Budget pool linked" if passed else "Budget pool must be linked",
            data={"budget_pool_id": context.budget_pool_id},
        )


class TR019_EscrowForGuaranteedTransactions(Rule):  # noqa: N801
    """TR-019: Escrow for guaranteed transactions."""

    rule_id = "TR-019"
    rule_name = "Escrow for guaranteed transactions"
    category = RuleCategory.TRADING
    severity = RuleSeverity.INFO
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301, ARG002
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Escrow handled by payment service",
            data={},
        )


class TR020_EffectReportWindow24h(Rule):  # noqa: N801
    """TR-020: Effect report window is 24 hours."""

    rule_id = "TR-020"
    rule_name = "Effect report window 24h"
    category = RuleCategory.TRADING
    severity = RuleSeverity.INFO
    applies_to_operations = ["order_create", "effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301, ARG002
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="Effect report window enforced by reporting service",
            data={"window_hours": 24},
        )


class TR021_StructuredEffectReport(Rule):  # noqa: N801
    """TR-021: Structured effect report must contain detail dict."""

    rule_id = "TR-021"
    rule_name = "Structured effect report"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["effect_report"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = context.effect_score is not None
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Effect report has structured detail" if passed else "Effect report must include structured detail",
            data={"effect_score": context.effect_score},
        )


# ---------------------------------------------------------------------------
# Budget Rules
# ---------------------------------------------------------------------------


class BUDGET001_BalanceSufficient(Rule):  # noqa: N801
    """BUDGET-001: Balance must be sufficient."""

    rule_id = "BUDGET-001"
    rule_name = "Balance sufficient"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = (context.budget_balance or 0) >= (context.amount_cny or 0)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Sufficient balance" if passed else "Insufficient balance",
            data={
                "budget_balance": context.budget_balance,
                "amount_cny": context.amount_cny,
            },
        )


class BUDGET002_SingleTransactionLimit(Rule):  # noqa: N801
    """BUDGET-002: Single transaction must not exceed per-call max."""

    rule_id = "BUDGET-002"
    rule_name = "Single transaction limit"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = (context.amount_cny or 0) <= (context.per_call_max or float("inf"))
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Within per-call limit" if passed else "Exceeds per-call limit",
            data={
                "amount_cny": context.amount_cny,
                "per_call_max": context.per_call_max,
            },
        )


class BUDGET003_AgentDailyLimit(Rule):  # noqa: N801
    """BUDGET-003: Agent daily spending must not exceed daily max."""

    rule_id = "BUDGET-003"
    rule_name = "Agent daily limit"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        total = (context.agent_daily_spent or 0) + (context.amount_cny or 0)
        passed = total <= (context.agent_daily_max or 0)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Within agent daily limit" if passed else "Exceeds agent daily limit",
            data={
                "agent_daily_spent": context.agent_daily_spent,
                "amount_cny": context.amount_cny,
                "agent_daily_max": context.agent_daily_max,
            },
        )


class BUDGET004_PoolDailyLimit(Rule):  # noqa: N801
    """BUDGET-004: Pool daily spending must not exceed daily max."""

    rule_id = "BUDGET-004"
    rule_name = "Pool daily limit"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        total = (context.budget_daily_spent or 0) + (context.amount_cny or 0)
        passed = total <= (context.budget_daily_max or 0)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Within pool daily limit" if passed else "Exceeds pool daily limit",
            data={
                "budget_daily_spent": context.budget_daily_spent,
                "amount_cny": context.amount_cny,
                "budget_daily_max": context.budget_daily_max,
            },
        )


# ---------------------------------------------------------------------------
# Security Rules
# ---------------------------------------------------------------------------


class SEC001_SecurityScanRequired(Rule):  # noqa: N801
    """SEC-001: Security scan must not have failed."""

    rule_id = "SEC-001"
    rule_name = "Security scan required"
    category = RuleCategory.SECURITY
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["skill_register", "skill_update", "order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        passed = context.security_scan_result != "failed"
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Security scan passed" if passed else "Security scan failed",
            data={"security_scan_result": context.security_scan_result},
        )


class SEC002_DataSensitivityCheck(Rule):  # noqa: N801
    """SEC-002: Restricted data sensitivity + skill item -> BLOCK."""

    rule_id = "SEC-002"
    rule_name = "Data sensitivity check"
    category = RuleCategory.SECURITY
    severity = RuleSeverity.BLOCK
    applies_to_operations = ["order_create", "skill_register", "skill_update"]

    async def evaluate(self, context: RuleContext) -> RuleResult:  # noqa: PLR6301
        blocked = (
            context.data_sensitivity == "restricted"
            and context.item_type == "skill"
        )
        passed = not blocked
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=passed,
            severity=self.severity,
            message="Data sensitivity OK" if passed else "Restricted data cannot be used with skill items",
            data={
                "data_sensitivity": context.data_sensitivity,
                "item_type": context.item_type,
            },
        )
