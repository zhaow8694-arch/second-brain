from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

from .schemas import EffectReport

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

_BASE_SCORE = 50.0
_EFFECT_AVG_MAX_BONUS = 20.0
_CERTIFICATION_BONUS = 10.0
_COMPLAINT_PENALTY = 15.0
_WEEKLY_DECAY_RATE = 0.05  # 5% per week


class TrustScorer:
    """Dynamic trust scoring engine for items and providers.

    The trust score is calculated as:

        score = base_50
              + effect_avg_bonus (max +20)
              + certification_bonus (+10 if certified)
              - complaint_penalty (-15 each)
              - time_decay (5% per week on cumulative deltas)

    Provider scores are the average of all their item scores plus a
    transaction-volume bonus.
    """

    # ------------------------------------------------------------------
    # Item scoring
    # ------------------------------------------------------------------

    async def calculate_item_score(
        self,
        item_id: UUID,
        repo: Any,
    ) -> float:
        """Calculate the trust score for a single catalog item.

        Args:
            item_id: The catalog item to score.
            repo: Repository providing access to trust events and items.

        Returns:
            The computed trust score (clamped to [0, 100]).
        """
        events = await repo.get_trust_events(
            target_type="item", target_id=item_id
        )

        effect_scores: list[float] = []
        complaint_count = 0
        is_certified = False

        for event in events:
            if event.event_type == "effect_report":
                data = event.event_data or {}
                score = data.get("effect_score", 0)
                effect_scores.append(float(score))
            elif event.event_type == "complaint":
                complaint_count += 1
            elif event.event_type == "certification":
                data = event.event_data or {}
                if data.get("approved", False):
                    is_certified = True

        # Effect average bonus: scale from [0,5] → [0, +20]
        effect_avg_bonus = 0.0
        if effect_scores:
            avg = sum(effect_scores) / len(effect_scores)
            effect_avg_bonus = (avg / 5.0) * _EFFECT_AVG_MAX_BONUS

        # Certification bonus
        cert_bonus = _CERTIFICATION_BONUS if is_certified else 0.0

        # Complaint penalty
        complaint_pen = complaint_count * _COMPLAINT_PENALTY

        # Time decay on net delta
        net_delta = effect_avg_bonus + cert_bonus - complaint_pen
        decayed_delta = self._apply_decay(net_delta, events)

        score = _BASE_SCORE + decayed_delta
        score = max(0.0, min(100.0, score))

        logger.debug(
            "calculate_item_score",
            item_id=str(item_id),
            effect_avg_bonus=effect_avg_bonus,
            cert_bonus=cert_bonus,
            complaint_pen=complaint_pen,
            decayed_delta=decayed_delta,
            final_score=score,
        )

        return score

    # ------------------------------------------------------------------
    # Provider scoring
    # ------------------------------------------------------------------

    async def calculate_provider_score(
        self,
        provider_id: UUID,
        repo: Any,
    ) -> float:
        """Calculate the trust score for a provider.

        Computed as the average of all active item scores plus a
        transaction-volume bonus.

        Transaction-volume bonus:
            +2 for >= 10 transactions
            +5 for >= 50 transactions
            +8 for >= 200 transactions
        """
        item_ids = await repo.get_provider_item_ids(provider_id)
        if not item_ids:
            return _BASE_SCORE

        item_scores: list[float] = []
        total_tx = 0
        for iid in item_ids:
            score = await self.calculate_item_score(iid, repo)
            item_scores.append(score)
            item = await repo.get_catalog_item(iid)
            if item:
                total_tx += item.total_transactions

        avg_score = sum(item_scores) / len(item_scores)

        # Transaction volume bonus
        vol_bonus = 0.0
        if total_tx >= 200:
            vol_bonus = 8.0
        elif total_tx >= 50:
            vol_bonus = 5.0
        elif total_tx >= 10:
            vol_bonus = 2.0

        score = avg_score + vol_bonus
        score = max(0.0, min(100.0, score))

        logger.debug(
            "calculate_provider_score",
            provider_id=str(provider_id),
            avg_item_score=avg_score,
            vol_bonus=vol_bonus,
            final_score=score,
        )

        return score

    # ------------------------------------------------------------------
    # Effect report processing
    # ------------------------------------------------------------------

    async def process_effect_report(
        self,
        report: EffectReport,
        repo: Any,
    ) -> float:
        """Process an effect report and update the item's trust score.

        Calculates the score delta from the effect report, creates a
        TrustEvent, and returns the delta.

        Returns:
            The score delta applied.
        """
        # Delta: scale effect_score (0-5) into a positive or negative delta
        # High scores increase trust, low scores decrease it
        if report.success:
            delta = (report.effect_score / 5.0) * 4.0  # max +4 per report
        else:
            delta = -(5 - report.effect_score) * 2.0  # max -10 per report

        # Latency deviation penalty
        if report.actual_latency_ms and report.declared_latency_ms:
            if report.declared_latency_ms > 0:
                latency_ratio = report.actual_latency_ms / report.declared_latency_ms
                if latency_ratio > 1.5:
                    delta -= 2.0  # penalty for significant latency deviation

        # Create TrustEvent
        event_data = {
            "effect_score": report.effect_score,
            "success": report.success,
            "transaction_id": str(report.transaction_id),
            "agent_id": str(report.agent_id),
        }
        if report.actual_latency_ms:
            event_data["actual_latency_ms"] = report.actual_latency_ms
        if report.declared_latency_ms:
            event_data["declared_latency_ms"] = report.declared_latency_ms
        if report.detail:
            event_data["detail"] = report.detail

        await repo.create_trust_event(
            target_type="item",
            target_id=report.item_id,
            event_type="effect_report",
            event_data=event_data,
            score_delta=delta,
        )

        logger.info(
            "effect_report_processed",
            item_id=str(report.item_id),
            effect_score=report.effect_score,
            success=report.success,
            score_delta=delta,
        )

        return delta

    # ------------------------------------------------------------------
    # Time decay
    # ------------------------------------------------------------------

    async def decay_scores(self, repo: Any) -> int:
        """Apply weekly time decay to all trust score deltas.

        Reduces the magnitude of each existing delta by 5% per week
        since the event was created.

        Returns:
            Number of events decayed.
        """
        events = await repo.get_all_trust_events()
        now = datetime.now(UTC)
        decayed = 0

        for event in events:
            age_days = (now - event.created_at).days
            age_weeks = age_days / 7.0
            decay_factor = (1 - _WEEKLY_DECAY_RATE) ** age_weeks

            new_delta = event.score_delta * decay_factor
            if abs(new_delta - event.score_delta) > 0.01:
                await repo.update_trust_event_delta(event.id, new_delta)
                decayed += 1

        logger.info("trust_scores_decayed", events_decayed=decayed)
        return decayed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_decay(self, net_delta: float, events: list[Any]) -> float:
        """Apply time-weighted decay to the net delta.

        Uses the age of the most recent event as a proxy for
        how much the aggregate delta should be attenuated.
        """
        if not events or net_delta == 0:
            return net_delta

        now = datetime.now(UTC)
        # Use the newest event's age as reference
        newest = max(events, key=lambda e: e.created_at)
        age_weeks = (now - newest.created_at).days / 7.0
        decay_factor = (1 - _WEEKLY_DECAY_RATE) ** age_weeks

        return net_delta * decay_factor
