"""Tests for the rules engine."""

from __future__ import annotations

import pytest

from aimart.domains.rules.engine import (
    Rule,
    RuleCategory,
    RuleContext,
    RuleResult,
    RulesEngine,
    RuleSeverity,
)


class AlwaysBlockRule(Rule):
    """Test rule that always blocks."""
    rule_id = "TEST-001"
    rule_name = "always_block"
    category = RuleCategory.TRADING
    severity = RuleSeverity.BLOCK
    applies_to_operations: list[str] = []

    async def evaluate(self, context: RuleContext) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=False,
            severity=self.severity,
            message="Always blocks",
        )


class AlwaysPassRule(Rule):
    """Test rule that always passes."""
    rule_id = "TEST-002"
    rule_name = "always_pass"
    category = RuleCategory.BUDGET
    severity = RuleSeverity.BLOCK
    applies_to_operations: list[str] = []

    async def evaluate(self, context: RuleContext) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=True,
            severity=self.severity,
            message="",
        )


class OperationSpecificRule(Rule):
    """Test rule that only applies to specific operations."""
    rule_id = "TEST-003"
    rule_name = "order_only"
    category = RuleCategory.TRADING
    severity = RuleSeverity.WARNING
    applies_to_operations = ["order_create"]

    async def evaluate(self, context: RuleContext) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            passed=False,
            severity=self.severity,
            message="Only applies to order_create",
        )


class TestRulesEngine:
    """Test the rules engine core functionality."""

    @pytest.mark.asyncio
    async def test_all_rules_pass(self):
        """When all rules pass, blocked=False."""
        engine = RulesEngine()
        engine.register(AlwaysPassRule())

        context = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="order_create",
        )
        result = await engine.evaluate(context)
        assert result.blocked is False
        assert len(result.results) == 1
        assert result.results[0].passed is True

    @pytest.mark.asyncio
    async def test_blocking_rule_triggers_block(self):
        """When a blocking rule fails, blocked=True."""
        engine = RulesEngine()
        engine.register(AlwaysBlockRule())

        context = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="order_create",
        )
        result = await engine.evaluate(context)
        assert result.blocked is True
        assert "TEST-001" in result.blocked_by

    @pytest.mark.asyncio
    async def test_operation_filtering(self):
        """Rules should only apply to matching operations."""
        engine = RulesEngine()
        engine.register(OperationSpecificRule())

        # This operation should NOT trigger the rule
        context = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="item_list",
        )
        result = await engine.evaluate(context)
        assert len(result.results) == 0  # Rule not applied

        # This operation SHOULD trigger the rule
        context2 = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="order_create",
        )
        result2 = await engine.evaluate(context2)
        assert len(result2.results) == 1

    @pytest.mark.asyncio
    async def test_warning_does_not_block(self):
        """Severity WARNING should not block."""
        engine = RulesEngine()
        rule = OperationSpecificRule()
        rule.severity = RuleSeverity.WARNING
        engine.register(rule)

        context = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="order_create",
        )
        result = await engine.evaluate(context)
        assert result.blocked is False
        assert "TEST-003" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_multiple_rules(self):
        """Multiple rules evaluated in sequence."""
        engine = RulesEngine()
        engine.register(AlwaysPassRule())
        engine.register(AlwaysBlockRule())

        context = RuleContext(
            actor_type="agent",
            actor_id="agent-1",
            operation="order_create",
        )
        result = await engine.evaluate(context)
        assert result.blocked is True
        assert len(result.results) == 2
