from __future__ import annotations

from urllib.parse import urlparse

import structlog

from .schemas import AgentCardValidationResult

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REQUIRED_AGENTCARD_SECTIONS = [
    "identity",
    "capability_declaration",
    "performance_declaration",
    "pricing",
    "delivery",
    "trust",
]

_VALID_PRICING_MODELS = {
    "per_call",
    "per_token",
    "per_task",
    "subscription",
    "revenue_share",
    "flat",
    "tiered",
    "freemium",
}


# ---------------------------------------------------------------------------
# Stage 1 – Schema Validation
# ---------------------------------------------------------------------------

def _validate_schema(agentcard: dict, item_type: str) -> list[str]:
    """Check that the AgentCard has all required top-level sections and
    that key fields match the declared item_type."""
    errors: list[str] = []

    # Required sections
    for section in _REQUIRED_AGENTCARD_SECTIONS:
        if section not in agentcard or agentcard[section] is None:
            errors.append(f"Missing required section: {section}")

    # item_type must match identity.item_type
    identity = agentcard.get("identity", {})
    if identity and identity.get("item_type") != item_type:
        errors.append(
            f"agentcard.identity.item_type '{identity.get('item_type')}' "
            f"does not match declared item_type '{item_type}'"
        )

    # pricing.model must be a recognised value
    pricing = agentcard.get("pricing", {})
    if pricing:
        model = pricing.get("model")
        if model and model not in _VALID_PRICING_MODELS:
            errors.append(
                f"Invalid pricing model '{model}'. "
                f"Valid: {', '.join(sorted(_VALID_PRICING_MODELS))}"
            )

    # performance_declaration must have at least one benchmark
    perf = agentcard.get("performance_declaration", {})
    if perf:
        benchmarks = perf.get("benchmarks")
        if not benchmarks or (isinstance(benchmarks, list) and len(benchmarks) < 1):
            errors.append(
                "performance_declaration.benchmarks must have at least 1 benchmark"
            )

    return errors


# ---------------------------------------------------------------------------
# Stage 2 – Semantic Validation
# ---------------------------------------------------------------------------

def _validate_semantic(agentcard: dict) -> list[str]:
    """Check that declared performance values are reasonable and that
    pricing / delivery / capability data is internally consistent."""
    errors: list[str] = []

    # Performance declared values should not exceed verified by >110%
    perf = agentcard.get("performance_declaration", {})
    if perf:
        benchmarks = perf.get("benchmarks", [])
        for bm in benchmarks:
            if isinstance(bm, dict):
                declared = bm.get("declared_value")
                verified = bm.get("verified_value")
                if declared is not None and verified is not None and verified != 0:
                    ratio = declared / verified
                    if ratio > 1.10:
                        errors.append(
                            f"Benchmark '{bm.get('name', 'unnamed')}' declared "
                            f"value exceeds verified by >110% "
                            f"(ratio={ratio:.2f})"
                        )

    # Pricing must have at least one non-null price detail
    pricing = agentcard.get("pricing", {})
    if pricing:
        price_details = pricing.get("details", [])
        if not price_details or not isinstance(price_details, list):
            errors.append("pricing.details must contain at least one price entry")
        else:
            has_valid = any(
                isinstance(d, dict) and any(
                    v is not None for v in d.values()
                )
                for d in price_details
            )
            if not has_valid:
                errors.append(
                    "pricing.details must have at least one entry with a non-null value"
                )

    # delivery.api_endpoint must be a valid URL
    delivery = agentcard.get("delivery", {})
    if delivery:
        endpoint = delivery.get("api_endpoint", "")
        if endpoint:
            parsed = urlparse(endpoint)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(
                    f"delivery.api_endpoint is not a valid URL: '{endpoint}'"
                )

    # capability_declaration.domains must be non-empty
    cap = agentcard.get("capability_declaration", {})
    if cap:
        domains = cap.get("domains", [])
        if not domains or (isinstance(domains, list) and len(domains) == 0):
            errors.append("capability_declaration.domains must be non-empty")

    return errors


# ---------------------------------------------------------------------------
# Stage 3 – Security Scan
# ---------------------------------------------------------------------------

def _security_scan(agentcard: dict, item_type: str) -> tuple[str, list[str]]:
    """Security-focused scan. Returns (result, warnings).

    result is one of 'clean', 'warning', 'failed'.
    """
    warnings: list[str] = []

    # For skills, sandbox_verified must be True
    if item_type == "skill":
        identity = agentcard.get("identity", {})
        if not identity.get("sandbox_verified", False):
            warnings.append(
                "Skill item does not have sandbox_verified=True – "
                "sandbox execution is not confirmed"
            )

    # Check data_access_declaration
    data_access = agentcard.get("data_access_declaration")
    if data_access is not None:
        if not isinstance(data_access, dict):
            return "failed", warnings + [
                "data_access_declaration must be a dict if present"
            ]
        # Reasonableness check: no wildcard access
        reads = data_access.get("reads", [])
        writes = data_access.get("writes", [])
        if "*" in reads or "*" in writes:
            warnings.append(
                "data_access_declaration contains wildcard ('*') access – "
                "consider restricting"
            )

    if warnings:
        return "warning", warnings
    return "clean", warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_agentcard(agentcard: dict, item_type: str) -> AgentCardValidationResult:
    """Run the full three-stage validation pipeline on an AgentCard.

    Stages:
      1. Schema validation – required sections, type consistency.
      2. Semantic validation – value reasonableness, URL format.
      3. Security scan – sandbox verification, data access checks.

    Returns an AgentCardValidationResult with aggregated errors, warnings,
    and a security scan outcome.
    """
    all_errors: list[str] = []
    all_warnings: list[str] = []

    # Stage 1
    schema_errors = _validate_schema(agentcard, item_type)
    all_errors.extend(schema_errors)
    logger.debug(
        "agentcard_validation_stage1",
        item_type=item_type,
        errors=len(schema_errors),
    )

    # Stage 2 (only if Stage 1 passed)
    if not all_errors:
        semantic_errors = _validate_semantic(agentcard)
        all_errors.extend(semantic_errors)
        logger.debug(
            "agentcard_validation_stage2",
            item_type=item_type,
            errors=len(semantic_errors),
        )
    else:
        logger.debug(
            "agentcard_validation_stage2_skipped",
            reason="stage1_errors",
        )

    # Stage 3
    security_result, security_warnings = _security_scan(agentcard, item_type)
    all_warnings.extend(security_warnings)
    logger.debug(
        "agentcard_validation_stage3",
        item_type=item_type,
        security_result=security_result,
        warnings=len(security_warnings),
    )

    valid = len(all_errors) == 0 and security_result != "failed"

    result = AgentCardValidationResult(
        valid=valid,
        errors=all_errors,
        warnings=all_warnings,
        security_scan_result=security_result,
    )

    logger.info(
        "agentcard_validation_complete",
        item_type=item_type,
        valid=result.valid,
        errors=len(result.errors),
        warnings=len(result.warnings),
        security_scan_result=result.security_scan_result,
    )

    return result
