from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import structlog
from elasticsearch import AsyncElasticsearch

from aimart.domains.search.schemas import (
    CapabilityNeed,
    MatchedItem,
    MatchedItemScore,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class MatcherConfig:
    """Tuning knobs for the two-stage capability matching engine."""

    max_results: int = 20
    min_composite_score: float = 0.3
    domain_match_boost: float = 1.5
    task_match_boost: float = 2.0
    es_min_score: float = 0.1


# ---------------------------------------------------------------------------
# Capability matcher
# ---------------------------------------------------------------------------


class CapabilityMatcher:
    """Two-stage capability matching engine.

    Stage 1 – Elasticsearch candidate retrieval:
        Build a bool query from the agent's ``CapabilityNeed`` that filters
        on item_type, status, domains, languages and applies boosts for
        domain / pricing-model matches.

    Stage 2 – In-process scoring:
        Each candidate is scored across five dimensions (capability,
        performance, price, trust, availability).  The composite score
        is a weighted sum using the agent's ``scoring_weights``.
    """

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        config: MatcherConfig | None = None,
    ) -> None:
        self._es = es_client
        self._config = config or MatcherConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def match(
        self,
        need: CapabilityNeed,
        agent_id: uuid.UUID,
    ) -> list[MatchedItem]:
        """Execute a two-stage match and return scored, ranked results."""
        # Stage 1: ES candidate retrieval
        candidates = await self._es_candidates(need)
        if not candidates:
            logger.info(
                "matcher.no_candidates",
                agent_id=str(agent_id),
                need_type=need.need_type,
            )
            return []

        # Stage 2: Score and rank
        scored = self._score_candidates(need, candidates)

        # Filter by minimum composite score and truncate
        results = [
            item
            for item in scored
            if item.scores.composite >= self._config.min_composite_score
        ]
        results = results[: self._config.max_results]

        logger.info(
            "matcher.match_complete",
            agent_id=str(agent_id),
            need_type=need.need_type,
            candidates=len(candidates),
            results=len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Stage 1: Elasticsearch candidate retrieval
    # ------------------------------------------------------------------

    async def _es_candidates(
        self, need: CapabilityNeed
    ) -> list[dict[str, Any]]:
        """Build and execute an ES bool query to retrieve candidate items."""
        must_clauses: list[dict[str, Any]] = [
            {"term": {"item_type": need.need_type}},
            {"term": {"status": "active"}},
        ]

        # Domains: at least one domain must match
        if need.domains:
            must_clauses.append({"terms": {"domains": need.domains}})

        # Languages filter
        if need.supported_languages:
            must_clauses.append(
                {"terms": {"supported_languages": need.supported_languages}}
            )

        should_clauses: list[dict[str, Any]] = []

        # Domain match boost
        if need.domains:
            should_clauses.append(
                {
                    "terms": {
                        "domains": need.domains,
                        "boost": self._config.domain_match_boost,
                    }
                }
            )

        # Pricing model preference boost
        if need.budget and need.budget.preferred_pricing_model:
            should_clauses.append(
                {
                    "term": {
                        "pricing_model": {
                            "value": need.budget.preferred_pricing_model,
                            "boost": 1.2,
                        }
                    }
                }
            )

        filter_clauses: list[dict[str, Any]] = []

        # Performance filters
        if need.performance:
            if need.performance.latency_p50_ms_max is not None:
                filter_clauses.append(
                    {"range": {"latency_p50_ms": {"lte": need.performance.latency_p50_ms_max}}}
                )
            if need.performance.latency_p99_ms_max is not None:
                filter_clauses.append(
                    {"range": {"latency_p99_ms": {"lte": need.performance.latency_p99_ms_max}}}
                )
            if need.performance.throughput_rps_min is not None:
                filter_clauses.append(
                    {"range": {"throughput_rps": {"gte": need.performance.throughput_rps_min}}}
                )
            if need.performance.availability_sla_min is not None:
                filter_clauses.append(
                    {"range": {"availability_sla": {"gte": need.performance.availability_sla_min}}}
                )

        # Price filters
        if need.budget:
            if need.budget.max_price_per_call is not None:
                filter_clauses.append(
                    {"range": {"price_max": {"lte": need.budget.max_price_per_call}}}
                )
            if need.budget.max_price_per_hour is not None:
                filter_clauses.append(
                    {"range": {"price_max": {"lte": need.budget.max_price_per_hour}}}
                )

        # Trust filters
        if need.trust:
            if need.trust.min_trust_score is not None:
                filter_clauses.append(
                    {"range": {"trust_score": {"gte": need.trust.min_trust_score}}}
                )
            if need.trust.certification_required:
                filter_clauses.append({"exists": {"field": "certification_status"}})

        # Assemble bool query
        bool_query: dict[str, Any] = {"must": must_clauses}
        if should_clauses:
            bool_query["should"] = should_clauses
            bool_query["minimum_should_match"] = 0
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        query: dict[str, Any] = {
            "query": {"bool": bool_query},
            "min_score": self._config.es_min_score,
            "size": self._config.max_results * 3,  # over-fetch for scoring
        }

        try:
            from aimart.domains.search.indexer import CAPABILITY_INDEX_NAME

            resp = await self._es.search(index=CAPABILITY_INDEX_NAME, body=query)
        except Exception as exc:
            logger.error("matcher.es_query_failed", error=str(exc))
            return []

        hits = resp.get("hits", {}).get("hits", [])
        candidates = [hit["_source"] for hit in hits]

        logger.debug(
            "matcher.es_candidates_retrieved",
            total=len(candidates),
            need_type=need.need_type,
        )
        return candidates

    # ------------------------------------------------------------------
    # Stage 2: Scoring
    # ------------------------------------------------------------------

    def _score_candidates(
        self,
        need: CapabilityNeed,
        candidates: list[dict[str, Any]],
    ) -> list[MatchedItem]:
        """Score each candidate across five dimensions and rank by composite."""
        scored_items: list[MatchedItem] = []

        for candidate in candidates:
            cap_score = self._score_capability(need, candidate)
            perf_score = self._score_performance(need, candidate)
            price_score = self._score_price(need, candidate)
            trust_score = self._score_trust(need, candidate)
            avail_score = self._score_availability(need, candidate)

            # Composite = weighted sum
            weights = need.scoring_weights
            composite = (
                weights["capability_match"] * cap_score
                + weights["performance"] * perf_score
                + weights["price"] * price_score
                + weights["trust"] * trust_score
                + weights["availability"] * avail_score
            )
            # Clamp to [0, 1]
            composite = max(0.0, min(1.0, composite))

            scores = MatchedItemScore(
                capability_match=round(cap_score, 4),
                performance=round(perf_score, 4),
                price=round(price_score, 4),
                trust=round(trust_score, 4),
                availability=round(avail_score, 4),
                composite=round(composite, 4),
            )

            # Determine matched domains and task types
            candidate_domains: list[str] = candidate.get("domains", []) or []
            matched_domains = [d for d in candidate_domains if d in need.domains]

            # Handle nested task_types from ES
            raw_task_types = candidate.get("task_types", []) or []
            candidate_task_names: list[str] = []
            for tt in raw_task_types:
                if isinstance(tt, str):
                    candidate_task_names.append(tt)
                elif isinstance(tt, dict):
                    candidate_task_names.append(tt.get("name", ""))

            item_id = candidate.get("item_id", "")
            matched_item = MatchedItem(
                item_id=uuid.UUID(item_id) if item_id else uuid.uuid4(),
                item_name=candidate.get("item_name", ""),
                item_type=candidate.get("item_type", ""),
                item_version=candidate.get("item_version"),
                provider_id=uuid.UUID(
                    candidate.get("provider_id")
                    or "00000000-0000-0000-0000-000000000000"
                ),
                provider_name=candidate.get("provider_name", ""),
                matched_domains=matched_domains,
                matched_task_types=candidate_task_names,
                performance_summary={
                    "latency_p50_ms": candidate.get("latency_p50_ms"),
                    "latency_p99_ms": candidate.get("latency_p99_ms"),
                    "throughput_rps": candidate.get("throughput_rps"),
                    "availability_sla": candidate.get("availability_sla"),
                },
                pricing_summary={
                    "pricing_model": candidate.get("pricing_model"),
                    "price_min": candidate.get("price_min"),
                    "price_max": candidate.get("price_max"),
                    "currency": candidate.get("currency"),
                },
                trust_score=float(candidate.get("trust_score", 50.0)),
                certification_status=candidate.get("certification_status"),
                scores=scores,
                trial_available=candidate.get("trial_available", False),
                api_endpoint=candidate.get("api_endpoint"),
            )
            scored_items.append(matched_item)

        # Sort by composite score descending
        scored_items.sort(key=lambda m: m.scores.composite, reverse=True)
        return scored_items

    # ------------------------------------------------------------------
    # Individual dimension scorers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_capability(need: CapabilityNeed, candidate: dict[str, Any]) -> float:
        """Score domain overlap (0-0.5) + language match (0-0.3) + task type match (0-0.2).

        Domain overlap:
            Jaccard similarity of need.domains and candidate.domains, scaled to 0-0.5.

        Language match:
            If need.supported_languages is specified, proportion of required
            languages present in the candidate.  Otherwise 0.3 (full language
            score since no constraint).

        Task type match:
            Simple binary: 0.2 if any task_type overlap, 0.0 otherwise.
            If neither side specifies task types, 0.1 (partial credit).
        """
        # --- Domain overlap ---
        candidate_domains: set[str] = set(candidate.get("domains", []) or [])
        need_domains: set[str] = set(need.domains)
        if need_domains and candidate_domains:
            intersection = need_domains & candidate_domains
            union = need_domains | candidate_domains
            domain_score = 0.5 * (len(intersection) / len(union))
        else:
            domain_score = 0.0

        # --- Language match ---
        if need.supported_languages:
            candidate_langs: set[str] = set(
                candidate.get("supported_languages", []) or []
            )
            need_langs = set(need.supported_languages)
            if need_langs:
                lang_overlap = len(need_langs & candidate_langs) / len(need_langs)
                lang_score = 0.3 * lang_overlap
            else:
                lang_score = 0.0
        else:
            lang_score = 0.3  # no language constraint → full credit

        # --- Task type match ---
        raw_task_types = candidate.get("task_types", []) or []
        candidate_task_names: set[str] = set()
        for tt in raw_task_types:
            if isinstance(tt, str):
                candidate_task_names.add(tt)
            elif isinstance(tt, dict):
                candidate_task_names.add(tt.get("name", ""))

        if candidate_task_names and need.task_description:
            # Simple heuristic: if any task type keyword appears in the description
            desc_lower = need.task_description.lower()
            overlap = any(t.lower() in desc_lower for t in candidate_task_names if t)
            task_score = 0.2 if overlap else 0.0
        elif candidate_task_names or need.task_description:
            task_score = 0.1
        else:
            task_score = 0.1

        total = domain_score + lang_score + task_score
        return min(1.0, total)

    @staticmethod
    def _score_performance(
        need: CapabilityNeed, candidate: dict[str, Any]
    ) -> float:
        """Score performance fit.

        Base score 0.5.  Bonuses and penalties:
        - Latency p50 below constraint: +0.2, above: -0.15
        - Latency p99 below constraint: +0.15, above: -0.1
        - Availability above constraint: +0.15
        """
        score = 0.5
        perf = need.performance

        if perf:
            c_p50 = candidate.get("latency_p50_ms")
            if c_p50 is not None and perf.latency_p50_ms_max is not None:
                if c_p50 <= perf.latency_p50_ms_max:
                    score += 0.2
                else:
                    score -= 0.15

            c_p99 = candidate.get("latency_p99_ms")
            if c_p99 is not None and perf.latency_p99_ms_max is not None:
                if c_p99 <= perf.latency_p99_ms_max:
                    score += 0.15
                else:
                    score -= 0.1

            c_sla = candidate.get("availability_sla")
            if c_sla is not None and perf.availability_sla_min is not None:
                if c_sla >= perf.availability_sla_min:
                    score += 0.15

        return max(0.0, min(1.0, score))

    @staticmethod
    def _score_price(need: CapabilityNeed, candidate: dict[str, Any]) -> float:
        """Score price competitiveness.

        - Free / freemium items: 1.0
        - Within budget: 1.0 - (price / max_price) * 0.7
        - Over budget: 0.0
        - No budget constraint: 0.5 (neutral)
        """
        pricing_model = candidate.get("pricing_model") or ""
        if pricing_model.lower() in ("free", "freemium"):
            return 1.0

        price_max = candidate.get("price_max")
        budget = need.budget

        if budget is None:
            # No budget specified → neutral score
            return 0.5

        # Determine relevant budget ceiling
        budget_ceiling: float | None = None
        if pricing_model == "per_call" and budget.max_price_per_call is not None:
            budget_ceiling = budget.max_price_per_call
        elif pricing_model == "per_token" and budget.max_price_per_token is not None:
            budget_ceiling = budget.max_price_per_token
        elif pricing_model == "per_hour" and budget.max_price_per_hour is not None:
            budget_ceiling = budget.max_price_per_hour
        else:
            # Try any available ceiling
            budget_ceiling = (
                budget.max_price_per_call
                or budget.max_price_per_token
                or budget.max_price_per_hour
            )

        if budget_ceiling is None:
            return 0.5

        if price_max is None:
            return 0.3  # unknown price, slight penalty

        if price_max > budget_ceiling:
            return 0.0

        # Within budget: closer to 0 is better
        ratio = price_max / budget_ceiling
        return 1.0 - ratio * 0.7

    @staticmethod
    def _score_trust(need: CapabilityNeed, candidate: dict[str, Any]) -> float:
        """Score trust: trust_score/100 + certified bonus.

        - Base: trust_score / 100
        - If certification_status is present and not empty: +0.2
        - If trust.certification_required and not certified: -0.3 penalty
        """
        raw_trust = float(candidate.get("trust_score", 50.0))
        score = raw_trust / 100.0

        cert_status = candidate.get("certification_status")
        is_certified = bool(cert_status and cert_status not in ("none", "pending", ""))

        if is_certified:
            score += 0.2

        if need.trust and need.trust.certification_required and not is_certified:
            score -= 0.3

        return max(0.0, min(1.0, score))

    @staticmethod
    def _score_availability(
        need: CapabilityNeed, candidate: dict[str, Any]
    ) -> float:
        """Score availability: directly use the availability_sla value.

        Items without an SLA get a neutral 0.5 score.
        """
        sla = candidate.get("availability_sla")
        if sla is None:
            return 0.5
        return max(0.0, min(1.0, float(sla)))
