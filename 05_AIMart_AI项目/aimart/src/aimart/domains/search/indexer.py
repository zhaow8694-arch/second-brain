from __future__ import annotations

import uuid
from typing import Any

import structlog
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Elasticsearch index mapping for the capability catalog
# ---------------------------------------------------------------------------

CAPABILITY_INDEX_NAME = "aimart_capabilities"

CAPABILITY_INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "filter": {
                "domain_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                },
            },
            "analyzer": {
                "domain_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "domain_ngram_filter"],
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "item_id": {"type": "keyword"},
            "agentcard_version": {"type": "keyword"},
            "item_type": {"type": "keyword"},
            "item_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "search": {"type": "text", "analyzer": "domain_analyzer"},
                },
            },
            "item_version": {"type": "keyword"},
            "domains": {"type": "keyword"},
            "task_types": {
                "type": "nested",
                "properties": {
                    "name": {"type": "keyword"},
                    "description": {"type": "text"},
                },
            },
            "supported_languages": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "task_description": {"type": "text", "analyzer": "domain_analyzer"},
            "latency_p50_ms": {"type": "integer"},
            "latency_p99_ms": {"type": "integer"},
            "throughput_rps": {"type": "integer"},
            "availability_sla": {"type": "double"},
            "trust_score": {"type": "double"},
            "pricing_model": {"type": "keyword"},
            "price_min": {"type": "double"},
            "price_max": {"type": "double"},
            "currency": {"type": "keyword"},
            "status": {"type": "keyword"},
            "es_index_version": {"type": "integer"},
            "provider_id": {"type": "keyword"},
            "provider_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "certification_status": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        },
    },
}


class CapabilityIndexer:
    """Manages the Elasticsearch index for capability items.

    Provides methods to create and maintain the index, convert AgentCard
    documents into flat ES documents, and perform bulk operations.
    """

    def __init__(self, es_client: AsyncElasticsearch) -> None:
        self._es = es_client

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    async def ensure_index(self) -> None:
        """Create the capability index if it does not already exist."""
        exists = await self._es.indices.exists(index=CAPABILITY_INDEX_NAME)
        if exists:
            logger.debug("indexer.index_exists", index=CAPABILITY_INDEX_NAME)
            return

        await self._es.indices.create(
            index=CAPABILITY_INDEX_NAME,
            body=CAPABILITY_INDEX_MAPPING,
        )
        logger.info("indexer.index_created", index=CAPABILITY_INDEX_NAME)

    # ------------------------------------------------------------------
    # Single document indexing
    # ------------------------------------------------------------------

    async def index_agentcard(self, agentcard: dict[str, Any]) -> str:
        """Index a single AgentCard document into Elasticsearch.

        Parameters
        ----------
        agentcard:
            A dictionary representing the AgentCard JSON payload.

        Returns
        -------
        The Elasticsearch document ID (same as item_id).
        """
        doc = self._agentcard_to_doc(agentcard)
        item_id = doc["item_id"]

        await self._es.index(
            index=CAPABILITY_INDEX_NAME,
            id=item_id,
            body=doc,
            refresh="wait_for",
        )
        logger.info("indexer.document_indexed", item_id=item_id)
        return item_id

    # ------------------------------------------------------------------
    # Bulk indexing
    # ------------------------------------------------------------------

    async def bulk_index(self, agentcards: list[dict[str, Any]]) -> int:
        """Bulk-index a list of AgentCard documents.

        Returns the number of successfully indexed documents.
        """
        if not agentcards:
            return 0

        from elasticsearch.helpers import async_bulk

        actions = []
        for card in agentcards:
            doc = self._agentcard_to_doc(card)
            actions.append(
                {
                    "_index": CAPABILITY_INDEX_NAME,
                    "_id": doc["item_id"],
                    "_source": doc,
                }
            )

        success_count, errors = await async_bulk(
            self._es,
            actions,
            refresh="wait_for",
            raise_on_error=False,
        )

        if errors and isinstance(errors, list):
            logger.warning(
                "indexer.bulk_errors",
                error_count=len(errors),
                total=len(actions),
            )

        logger.info(
            "indexer.bulk_indexed",
            success=success_count,
            total=len(actions),
        )
        return success_count

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    async def remove_item(self, item_id: uuid.UUID) -> bool:
        """Delete a capability item from the Elasticsearch index.

        Returns True if the document was found and deleted.
        """
        try:
            result = await self._es.delete(
                index=CAPABILITY_INDEX_NAME,
                id=str(item_id),
                refresh="wait_for",
            )
            deleted = result.get("result") == "deleted"
            logger.info("indexer.item_removed", item_id=str(item_id), deleted=deleted)
            return deleted
        except Exception as exc:
            # NotFoundError or similar
            logger.warning(
                "indexer.item_remove_failed",
                item_id=str(item_id),
                error=str(exc),
            )
            return False

    # ------------------------------------------------------------------
    # Partial updates
    # ------------------------------------------------------------------

    async def update_trust_score(self, item_id: uuid.UUID, trust_score: float) -> bool:
        """Partially update the trust_score of an indexed item.

        Returns True if the update was acknowledged.
        """
        try:
            result = await self._es.update(
                index=CAPABILITY_INDEX_NAME,
                id=str(item_id),
                body={"doc": {"trust_score": trust_score}},
                refresh="wait_for",
            )
            success = result.get("result") in ("updated", "noop")
            logger.info(
                "indexer.trust_score_updated",
                item_id=str(item_id),
                trust_score=trust_score,
                success=success,
            )
            return success
        except Exception as exc:
            logger.warning(
                "indexer.trust_score_update_failed",
                item_id=str(item_id),
                error=str(exc),
            )
            return False

    # ------------------------------------------------------------------
    # Document conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _agentcard_to_doc(card: dict[str, Any]) -> dict[str, Any]:
        """Convert an AgentCard JSON payload into a flat Elasticsearch document.

        The AgentCard may contain deeply nested structures.  This method
        flattens the relevant fields for efficient ES queries.
        """
        # Extract nested performance metrics if present
        perf = card.get("performance", {}) or {}
        pricing = card.get("pricing", {}) or {}
        provider = card.get("provider", {}) or {}

        # Build task_types as nested objects for ES
        raw_task_types = card.get("task_types", []) or []
        task_types_nested: list[dict[str, str]] = []
        for tt in raw_task_types:
            if isinstance(tt, str):
                task_types_nested.append({"name": tt, "description": ""})
            elif isinstance(tt, dict):
                task_types_nested.append(
                    {
                        "name": tt.get("name", ""),
                        "description": tt.get("description", ""),
                    }
                )

        doc: dict[str, Any] = {
            "item_id": str(card.get("item_id", card.get("id", ""))),
            "agentcard_version": card.get("agentcard_version"),
            "item_type": card.get("item_type", ""),
            "item_name": card.get("name", card.get("item_name", "")),
            "item_version": card.get("version", card.get("item_version")),
            "domains": card.get("domains", []) or [],
            "task_types": task_types_nested,
            "supported_languages": card.get("supported_languages", []) or [],
            "tags": card.get("tags", []) or [],
            "task_description": card.get("task_description", ""),
            "latency_p50_ms": perf.get("latency_p50_ms"),
            "latency_p99_ms": perf.get("latency_p99_ms"),
            "throughput_rps": perf.get("throughput_rps"),
            "availability_sla": perf.get("availability_sla"),
            "trust_score": card.get("trust_score", 50.0),
            "pricing_model": pricing.get("model") or card.get("pricing_model"),
            "price_min": pricing.get("price_min") or card.get("price_min"),
            "price_max": pricing.get("price_max") or card.get("price_max"),
            "currency": pricing.get("currency") or card.get("currency"),
            "status": card.get("status", "active"),
            "es_index_version": card.get("es_index_version", 1),
            "provider_id": str(provider.get("id", provider.get("provider_id", ""))),
            "provider_name": provider.get("name", provider.get("provider_name", "")),
            "certification_status": card.get("certification_status"),
            "created_at": card.get("created_at"),
            "updated_at": card.get("updated_at"),
        }

        return doc
