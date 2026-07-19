from __future__ import annotations

from aimart.domains.rules.engine import Rule, RulesEngine
from aimart.domains.rules.trading_rules import (
    BUDGET001_BalanceSufficient,
    BUDGET002_SingleTransactionLimit,
    BUDGET003_AgentDailyLimit,
    BUDGET004_PoolDailyLimit,
    SEC001_SecurityScanRequired,
    SEC002_DataSensitivityCheck,
    TR001_MustProvideAgentCard,
    TR003_PerformanceDeclaration,
    TR006_SkillsPassSandboxScan,
    TR011_MustSearchBeforePurchase,
    TR017_OrderExpiresIn30s,
    TR018_MustLinkBudgetPool,
    TR019_EscrowForGuaranteedTransactions,
    TR020_EffectReportWindow24h,
    TR021_StructuredEffectReport,
)

# Convenience list of all default rule classes in canonical order.
DEFAULT_RULE_CLASSES: list[type[Rule]] = [
    TR001_MustProvideAgentCard,
    TR003_PerformanceDeclaration,
    TR006_SkillsPassSandboxScan,
    TR011_MustSearchBeforePurchase,
    TR017_OrderExpiresIn30s,
    TR018_MustLinkBudgetPool,
    TR019_EscrowForGuaranteedTransactions,
    TR020_EffectReportWindow24h,
    TR021_StructuredEffectReport,
    BUDGET001_BalanceSufficient,
    BUDGET002_SingleTransactionLimit,
    BUDGET003_AgentDailyLimit,
    BUDGET004_PoolDailyLimit,
    SEC001_SecurityScanRequired,
    SEC002_DataSensitivityCheck,
]


def create_default_engine() -> RulesEngine:
    """Create a RulesEngine with all 15 default rules registered.

    Returns:
        A fully configured RulesEngine instance.
    """
    engine = RulesEngine()
    for rule_cls in DEFAULT_RULE_CLASSES:
        engine.register(rule_cls())
    return engine


def create_engine_with_custom_rules(
    extra_rules: list[Rule] | None = None,
    exclude_rule_ids: list[str] | None = None,
) -> RulesEngine:
    """Create a RulesEngine with default rules, optionally adding or excluding rules.

    Args:
        extra_rules: Additional rule instances to register after defaults.
        exclude_rule_ids: Rule IDs to skip from the default set.

    Returns:
        A configured RulesEngine instance.
    """
    exclude = set(exclude_rule_ids or [])
    engine = RulesEngine()

    for rule_cls in DEFAULT_RULE_CLASSES:
        instance = rule_cls()
        if instance.rule_id not in exclude:
            engine.register(instance)

    for rule in (extra_rules or []):
        engine.register(rule)

    return engine
