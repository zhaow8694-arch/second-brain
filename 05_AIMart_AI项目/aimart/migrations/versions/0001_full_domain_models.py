"""Initial migration: create all domain models.

Revision ID: 0001
Revises: None
Create Date: 2026-06-07
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # Identity domain
    # -----------------------------------------------------------------------
    op.create_table(
        "participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("jurisdiction", sa.String(128), nullable=True),
        sa.Column("kyc_status", sa.String(20), nullable=False, default="pending"),
        sa.Column("kyc_documents", postgresql.JSONB(), nullable=True),
        sa.Column("kyc_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("totp_secret", sa.String(512), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_participants_email", "participants", ["email"])
    op.create_index("ix_participants_type_status", "participants", ["type", "status"])

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("framework", sa.String(32), nullable=False),
        sa.Column("framework_version", sa.String(32), nullable=True),
        sa.Column("capability_scope", postgresql.JSONB(), nullable=True),
        sa.Column("capability_scope_hash", sa.String(128), nullable=True),
        sa.Column("spending_authority_level", sa.String(2), nullable=False, default="L0"),
        sa.Column("budget_pool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trust_score", sa.Integer(), nullable=False, default=50),
        sa.Column("trust_score_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ip", sa.String(45), nullable=True),
        sa.Column("total_transactions", sa.Integer(), nullable=False, default=0),
        sa.Column("total_spent_cny", sa.Float(), nullable=False, default=0.0),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])
    op.create_index("ix_agents_owner_status", "agents", ["owner_id", "status"])
    op.create_index("ix_agents_trust_score", "agents", ["trust_score"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("key_prefix", sa.String(8), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("key_encrypted", sa.Text(), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("permissions", postgresql.JSONB(), nullable=False, default=dict),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, default=0),
        sa.Column("allowed_ips", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("allowed_origins", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_api_keys_participant_id", "api_keys", ["participant_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_participant_status", "api_keys", ["participant_id", "status"])

    op.create_table(
        "oauth2_clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", sa.String(128), nullable=False, unique=True),
        sa.Column("client_secret_hash", sa.String(128), nullable=False),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grant_types", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("redirect_uris", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_oauth2_clients_client_id", "oauth2_clients", ["client_id"])
    op.create_index("ix_oauth2_clients_owner_id", "oauth2_clients", ["owner_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("oauth2_client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("oauth2_clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_refresh_tokens_participant_id", "refresh_tokens", ["participant_id"])
    op.create_index("ix_refresh_tokens_participant_status", "refresh_tokens", ["participant_id", "status"])

    op.create_table(
        "mfa_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_type", sa.String(20), nullable=False),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False, default=3),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_mfa_challenges_participant_id", "mfa_challenges", ["participant_id"])
    op.create_index("ix_mfa_challenges_participant_status", "mfa_challenges", ["participant_id", "status"])
    op.create_index("ix_mfa_challenges_expires", "mfa_challenges", ["expires_at"])

    # -----------------------------------------------------------------------
    # Catalog domain
    # -----------------------------------------------------------------------
    op.create_table(
        "catalog_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agentcard", postgresql.JSONB(), nullable=False),
        sa.Column("agentcard_hash", sa.String(64), nullable=False),
        sa.Column("agentcard_schema_version", sa.String(16), nullable=True, default="1.0"),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("certification_status", sa.String(20), nullable=False, default="none"),
        sa.Column("trust_score", sa.Float(), nullable=False, default=50.0),
        sa.Column("total_transactions", sa.Integer(), nullable=False, default=0),
        sa.Column("total_revenue", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("is_featured", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_catalog_items_provider_id", "catalog_items", ["provider_id"])
    op.create_index("ix_catalog_items_item_type", "catalog_items", ["item_type"])
    op.create_index("ix_catalog_items_status", "catalog_items", ["status"])
    op.create_index("ix_catalog_items_trust_score", "catalog_items", ["trust_score"])

    op.create_table(
        "catalog_item_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("version_type", sa.String(16), nullable=False, default="patch"),
        sa.Column("agentcard", postgresql.JSONB(), nullable=False),
        sa.Column("agentcard_hash", sa.String(64), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("requires_reverification", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_catalog_item_versions_item_id", "catalog_item_versions", ["item_id"])
    op.create_unique_constraint("uq_catalog_item_versions_item_version", "catalog_item_versions", ["item_id", "version"])

    op.create_table(
        "pricing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pricing_model", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, default="CNY"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("billing_unit", sa.String(32), nullable=True),
        sa.Column("min_quantity", sa.Integer(), nullable=False, default=1),
        sa.Column("max_quantity", sa.Integer(), nullable=True),
        sa.Column("setup_fee", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_pricing_plans_item_id", "pricing_plans", ["item_id"])

    # -----------------------------------------------------------------------
    # Search domain
    # -----------------------------------------------------------------------
    op.create_table(
        "search_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=False),
        sa.Column("need_type", sa.String(20), nullable=False),
        sa.Column("domains", postgresql.JSONB(), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=True),
        sa.Column("constraints", postgresql.JSONB(), nullable=True),
        sa.Column("scoring_weights", postgresql.JSONB(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False, default=0),
        sa.Column("selected_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trial_initiated", sa.Integer(), nullable=False, default=0),
        sa.Column("purchased", sa.Integer(), nullable=False, default=0),
        sa.Column("query_latency_ms", sa.Integer(), nullable=False, default=0),
        sa.Column("match_latency_ms", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_search_queries_agent_id", "search_queries", ["agent_id"])
    op.create_index("ix_search_queries_need_type", "search_queries", ["need_type"])
    op.create_index("ix_search_queries_created_at", "search_queries", ["created_at"])

    op.create_table(
        "capability_indices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("agentcard_version", sa.String(32), nullable=True),
        sa.Column("item_type", sa.String(32), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=True),
        sa.Column("item_version", sa.String(64), nullable=True),
        sa.Column("domains", postgresql.JSONB(), nullable=False),
        sa.Column("task_types", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("supported_languages", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("tags", postgresql.JSONB(), nullable=False, default=list),
        sa.Column("latency_p50_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p99_ms", sa.Integer(), nullable=True),
        sa.Column("throughput_rps", sa.Integer(), nullable=True),
        sa.Column("availability_sla", sa.Float(), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=False, default=50.0),
        sa.Column("pricing_model", sa.String(64), nullable=True),
        sa.Column("price_min", sa.Float(), nullable=True),
        sa.Column("price_max", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("es_index_version", sa.Integer(), nullable=False, default=1),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("certification_status", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_capability_indices_item_id", "capability_indices", ["item_id"], unique=True)
    op.create_index("ix_capability_indices_item_type", "capability_indices", ["item_type"])
    op.create_index("ix_capability_indices_status", "capability_indices", ["status"])
    op.create_index("ix_capability_indices_trust_score", "capability_indices", ["trust_score"])

    op.create_table(
        "trial_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trial_count", sa.Integer(), nullable=False, default=0),
        sa.Column("last_trial_date", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_trial_limits_agent_id", "trial_limits", ["agent_id"])
    op.create_index("ix_trial_limits_item_id", "trial_limits", ["item_id"])
    op.create_unique_constraint("uq_trial_limits_agent_item", "trial_limits", ["agent_id", "item_id"])

    # -----------------------------------------------------------------------
    # Exchange domain
    # -----------------------------------------------------------------------
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trial_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_type", sa.String(32), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("item_version", sa.String(64), nullable=True),
        sa.Column("pricing_model", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, default="CNY"),
        sa.Column("quantity", sa.Integer(), nullable=False, default=1),
        sa.Column("status", sa.String(20), nullable=False, default="created"),
        sa.Column("budget_pool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("escrow_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("effect_score", sa.Integer(), nullable=True),
        sa.Column("effect_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_orders_agent_id", "orders", ["agent_id"])
    op.create_index("ix_orders_item_id", "orders", ["item_id"])
    op.create_index("ix_orders_provider_id", "orders", ["provider_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "trials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="requested"),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("performance_data", postgresql.JSONB(), nullable=True),
        sa.Column("sandbox_config", postgresql.JSONB(), nullable=False, default=lambda: {}),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_trials_agent_id", "trials", ["agent_id"])
    op.create_index("ix_trials_item_id", "trials", ["item_id"])
    op.create_index("ix_trials_status", "trials", ["status"])

    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delivery_method", sa.String(20), nullable=False),
        sa.Column("delivery_endpoint", sa.String(512), nullable=True),
        sa.Column("delivery_latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_data_size_bytes", sa.Integer(), nullable=True),
        sa.Column("output_data_size_bytes", sa.Integer(), nullable=True),
        sa.Column("data_sensitivity", sa.String(32), nullable=True, default="public"),
        sa.Column("status", sa.String(20), nullable=False, default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_deliveries_order_id", "deliveries", ["order_id"])

    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiator_type", sa.String(32), nullable=False),
        sa.Column("initiator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dispute_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=True),
        sa.Column("disputed_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="open"),
        sa.Column("resolution", sa.String(64), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_disputes_order_id", "disputes", ["order_id"])
    op.create_index("ix_disputes_status", "disputes", ["status"])

    # -----------------------------------------------------------------------
    # Payment domain
    # -----------------------------------------------------------------------
    op.create_table(
        "budget_pools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, default="CNY"),
        sa.Column("balance", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("frozen_amount", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("total_cap", sa.Numeric(18, 4), nullable=True),
        sa.Column("single_transaction_max", sa.Numeric(18, 4), nullable=False, default=500),
        sa.Column("daily_max", sa.Numeric(18, 4), nullable=False, default=2000),
        sa.Column("weekly_max", sa.Numeric(18, 4), nullable=False, default=10000),
        sa.Column("monthly_max", sa.Numeric(18, 4), nullable=False, default=30000),
        sa.Column("auto_recharge", sa.Boolean(), nullable=False, default=False),
        sa.Column("recharge_threshold", sa.Numeric(18, 4), nullable=True),
        sa.Column("recharge_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_budget_pools_owner_id", "budget_pools", ["owner_id"])
    op.create_index("ix_budget_pools_status", "budget_pools", ["status"])
    op.create_check_constraint("ck_budget_pool_balance_nonneg", "budget_pools", sa.text("balance >= 0"))
    op.create_check_constraint("ck_budget_pool_frozen_nonneg", "budget_pools", sa.text("frozen_amount >= 0"))

    op.create_table(
        "agent_budget_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("budget_pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("daily_max", sa.Numeric(18, 4), nullable=False, default=500),
        sa.Column("per_call_max", sa.Numeric(18, 4), nullable=False, default=1),
        sa.Column("daily_spent", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("daily_spent_date", sa.Date(), nullable=True),
        sa.Column("spending_authority_level", sa.String(2), nullable=False, default="L0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint("uq_agent_budget_allocations_agent_pool", "agent_budget_allocations", ["agent_id", "pool_id"])

    op.create_table(
        "payment_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("budget_pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, default="CNY"),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=False, default=0.03),
        sa.Column("commission_amount", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("provider_payout", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("settlement_channel", sa.String(20), nullable=False),
        sa.Column("escrow_status", sa.String(20), nullable=False, default="frozen"),
        sa.Column("escrow_frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escrow_released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorization_level", sa.String(2), nullable=True),
        sa.Column("authorization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorized_by", sa.String(255), nullable=True),
        sa.Column("effect_score", sa.Integer(), nullable=True),
        sa.Column("effect_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("failure_reason", sa.String(1024), nullable=True),
        sa.Column("external_settlement_id", sa.String(255), nullable=True),
        sa.Column("settlement_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_payment_transactions_order_id", "payment_transactions", ["order_id"])
    op.create_index("ix_payment_transactions_agent_id", "payment_transactions", ["agent_id"])
    op.create_index("ix_payment_transactions_provider_id", "payment_transactions", ["provider_id"])
    op.create_index("ix_payment_transactions_status", "payment_transactions", ["status"])
    op.create_index("ix_payment_transactions_escrow_status", "payment_transactions", ["escrow_status"])
    op.create_check_constraint("ck_payment_transaction_effect_score_range", "payment_transactions", sa.text("effect_score IS NULL OR (effect_score >= 0 AND effect_score <= 5)"))

    op.create_table(
        "authorization_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=True),
        sa.Column("item_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_channel", sa.String(20), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reject_reason", sa.String(1024), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_authorization_requests_owner_status", "authorization_requests", ["owner_id", "status"])
    op.create_index("ix_authorization_requests_expires_at", "authorization_requests", ["expires_at"])

    op.create_table(
        "daily_budget_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("budget_pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("daily_spent", sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column("transaction_count", sa.Integer(), nullable=False, default=0),
    )
    op.create_unique_constraint("uq_daily_budget_snapshots_pool_agent_date", "daily_budget_snapshots", ["pool_id", "agent_id", "snapshot_date"])

    op.create_table(
        "anomaly_detection_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("budget_pool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("anomaly_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, default="info"),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("auto_action_taken", sa.String(64), nullable=True),
        sa.Column("owner_notified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_anomaly_detection_events_agent", "anomaly_detection_events", ["agent_id"])
    op.create_index("ix_anomaly_detection_events_type", "anomaly_detection_events", ["anomaly_type"])

    # -----------------------------------------------------------------------
    # Trust domain
    # -----------------------------------------------------------------------
    op.create_table(
        "trust_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, default=50.0),
        sa.Column("score_components", postgresql.JSONB(), nullable=True),
        sa.Column("total_events", sa.Integer(), nullable=False, default=0),
        sa.Column("last_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint("uq_trust_scores_target", "trust_scores", ["target_type", "target_id"])
    op.create_index("ix_trust_scores_score", "trust_scores", ["score"])

    op.create_table(
        "trust_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("event_data", postgresql.JSONB(), nullable=False),
        sa.Column("score_before", sa.Float(), nullable=True),
        sa.Column("score_after", sa.Float(), nullable=True),
        sa.Column("score_delta", sa.Float(), nullable=False, default=0.0),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_trust_events_target", "trust_events", ["target_type", "target_id"])
    op.create_index("ix_trust_events_event_type", "trust_events", ["event_type"])
    op.create_index("ix_trust_events_created_at", "trust_events", ["created_at"])

    op.create_table(
        "certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("certifier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("certification_level", sa.String(32), nullable=False, default="platform_certified"),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("benchmark_results", postgresql.JSONB(), nullable=False),
        sa.Column("score_boost", sa.Float(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_certifications_item_id", "certifications", ["item_id"])
    op.create_index("ix_certifications_certifier_id", "certifications", ["certifier_id"])
    op.create_index("ix_certifications_status", "certifications", ["status"])

    op.create_table(
        "effect_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, default=True),
        sa.Column("effect_score", sa.Integer(), nullable=False, default=3),
        sa.Column("actual_latency_ms", sa.Integer(), nullable=True),
        sa.Column("declared_latency_ms", sa.Integer(), nullable=True),
        sa.Column("actual_cost", sa.Float(), nullable=True),
        sa.Column("declared_cost", sa.Float(), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_effect_reports_order_id", "effect_reports", ["order_id"])
    op.create_index("ix_effect_reports_agent_id", "effect_reports", ["agent_id"])
    op.create_index("ix_effect_reports_item_id", "effect_reports", ["item_id"])

    # -----------------------------------------------------------------------
    # Audit domain
    # -----------------------------------------------------------------------
    op.create_table(
        "audit_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("checkpoint_date", sa.String(10), nullable=False),
        sa.Column("first_log_id", sa.String(64), nullable=False),
        sa.Column("last_log_id", sa.String(64), nullable=False),
        sa.Column("entry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("first_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merkle_root", sa.String(64), nullable=False),
        sa.Column("previous_checkpoint_hash", sa.String(64), nullable=True),
        sa.Column("current_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_checkpoints_date", "audit_checkpoints", ["checkpoint_date"])
    op.create_index("ix_audit_checkpoints_last_log_id", "audit_checkpoints", ["last_log_id"])

    # -----------------------------------------------------------------------
    # Rules domain
    # -----------------------------------------------------------------------
    op.create_table(
        "rule_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.String(64), nullable=False, unique=True),
        sa.Column("rule_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False, default="block"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("applies_to_operations", postgresql.JSONB(), nullable=True, default=list),
        sa.Column("config", postgresql.JSONB(), nullable=True, default=dict),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("priority", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_rule_definitions_rule_id", "rule_definitions", ["rule_id"])
    op.create_index("ix_rule_definitions_category", "rule_definitions", ["category"])
    op.create_index("ix_rule_definitions_enabled", "rule_definitions", ["enabled"])

    op.create_table(
        "rule_execution_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(128), nullable=False),
        sa.Column("actor_type", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.String(128), nullable=True),
        sa.Column("context_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False, default="block"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_rule_execution_records_rule_id", "rule_execution_records", ["rule_id"])
    op.create_index("ix_rule_execution_records_operation", "rule_execution_records", ["operation"])
    op.create_index("ix_rule_execution_records_created_at", "rule_execution_records", ["created_at"])


def downgrade() -> None:
    """Drop all tables."""
    tables = [
        "rule_execution_records",
        "rule_definitions",
        "audit_checkpoints",
        "effect_reports",
        "certifications",
        "trust_events",
        "trust_scores",
        "anomaly_detection_events",
        "daily_budget_snapshots",
        "authorization_requests",
        "payment_transactions",
        "agent_budget_allocations",
        "budget_pools",
        "disputes",
        "deliveries",
        "trials",
        "orders",
        "trial_limits",
        "capability_indices",
        "search_queries",
        "pricing_plans",
        "catalog_item_versions",
        "catalog_items",
        "mfa_challenges",
        "refresh_tokens",
        "oauth2_clients",
        "api_keys",
        "agents",
        "participants",
    ]
    for table in tables:
        op.drop_table(table)
