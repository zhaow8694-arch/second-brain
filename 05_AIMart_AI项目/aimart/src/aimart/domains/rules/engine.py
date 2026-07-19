from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RuleSeverity(StrEnum):
    """Severity level of a rule violation."""

    INFO = "info"
    WARNING = "warning"
    BLOCK = "block"
    SUSPEND = "suspend"


class RuleCategory(StrEnum):
    """Category grouping for rules."""

    TRADING = "trading"
    BUDGET = "budget"
    SECURITY = "security"
    SLA = "sla"
    PRICING = "pricing"


# ---------------------------------------------------------------------------
# Context & Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RuleContext:
    """All context data available to rules during evaluation."""

    actor_type: str = ""
    actor_id: str = ""
    owner_id: str = ""
    operation: str = ""
    target_type: str = ""
    target_id: str = ""
    item_type: str = ""
    item_id: str = ""
    agentcard: Any = None
    order_id: str = ""
    amount_cny: float = 0.0
    pricing_model: str = ""
    budget_pool_id: str | None = None
    budget_balance: float = 0.0
    budget_daily_spent: float = 0.0
    budget_daily_max: float = 0.0
    budget_weekly_spent: float = 0.0
    budget_weekly_max: float = 0.0
    budget_monthly_spent: float = 0.0
    budget_monthly_max: float = 0.0
    per_call_max: float = 0.0
    agent_daily_spent: float = 0.0
    agent_daily_max: float = 0.0
    effect_score: float | None = None
    success: bool | None = None
    actual_latency_ms: float | None = None
    declared_latency_ms: float | None = None
    declaration_accuracy: float | None = None
    spending_authority_level: int | None = None
    security_scan_result: str = ""
    sandbox_verified: bool = False
    data_sensitivity: str = ""


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_id: str
    rule_name: str
    category: RuleCategory
    passed: bool
    severity: RuleSeverity
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleEvaluationResult:
    """Aggregated result from evaluating all applicable rules."""

    results: list[RuleResult] = field(default_factory=list)
    blocked: bool = False
    blocked_by: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    audit_events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, result: RuleResult) -> None:
        """Add a single rule result and update aggregate flags."""
        self.results.append(result)

        if not result.passed:
            if result.severity == RuleSeverity.BLOCK:
                self.blocked = True
                self.blocked_by.append(result.rule_id)
            elif result.severity == RuleSeverity.WARNING:
                self.warnings.append(f"{result.rule_id}: {result.message}")
            elif result.severity == RuleSeverity.SUSPEND:
                self.blocked = True
                self.blocked_by.append(result.rule_id)

            self.audit_events.append(
                {
                    "rule_id": result.rule_id,
                    "rule_name": result.rule_name,
                    "category": result.category.value,
                    "severity": result.severity.value,
                    "message": result.message,
                    "data": result.data,
                }
            )


# ---------------------------------------------------------------------------
# Rule abstract base class
# ---------------------------------------------------------------------------

class Rule(ABC):
    """Abstract base class for all rules."""

    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    applies_to_operations: list[str]

    def applies(self, context: RuleContext) -> bool:
        """Determine whether this rule applies to the given context.

        Default implementation checks if the operation is in the
        applies_to_operations list.  Subclasses may override for more
        sophisticated logic.
        """
        if not self.applies_to_operations:
            return True
        return context.operation in self.applies_to_operations

    @abstractmethod
    async def evaluate(self, context: RuleContext) -> RuleResult:
        """Evaluate the rule against the context and return a result."""
        ...


# ---------------------------------------------------------------------------
# Rules Engine
# ---------------------------------------------------------------------------

class RulesEngine:
    """Core rules engine that evaluates a set of registered rules.

    Rules are iterated in registration order. Non-applicable rules are
    skipped. Exceptions during evaluation are caught and recorded as
    failures so that one broken rule cannot bring down the engine.
    """

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule: Rule) -> None:
        """Register a rule with the engine."""
        self._rules.append(rule)
        logger.debug("rule_registered", rule_id=rule.rule_id, rule_name=rule.rule_name)

    async def evaluate(self, context: RuleContext) -> RuleEvaluationResult:
        """Evaluate all applicable rules against the context.

        Returns:
            Aggregated RuleEvaluationResult.
        """
        result = RuleEvaluationResult()

        for rule in self._rules:
            if not rule.applies(context):
                continue

            try:
                rule_result = await rule.evaluate(context)
                result.add(rule_result)
            except Exception as exc:
                logger.exception(
                    "rule_evaluation_error",
                    rule_id=rule.rule_id,
                    error=str(exc),
                )
                result.add(
                    RuleResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        category=rule.category,
                        passed=False,
                        severity=RuleSeverity.BLOCK,
                        message=f"Rule evaluation failed: {exc}",
                        data={"error": str(exc)},
                    )
                )

        return result


