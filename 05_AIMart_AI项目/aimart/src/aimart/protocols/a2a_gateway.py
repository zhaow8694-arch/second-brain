"""A2A (Agent-to-Agent) gateway for AIMart.

Facilitates direct communication and negotiation between AI agents on the
platform.  Maintains an in-memory registry of agent endpoints and supports
agent-agent negotiation flows for pricing, disputes, and SLA agreements.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentEndpoint:
    """Registry entry for an agent that can participate in A2A communication."""

    agent_id: str
    capabilities: list[str]
    endpoint_url: str | None = None
    registered_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NegotiationSession:
    """An active negotiation between two agents."""

    session_id: str
    agent_a: str
    agent_b: str
    topic: str
    status: str = "active"  # active | settled | failed | expired
    rounds: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    settled_at: float | None = None
    result: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# A2A Gateway
# ---------------------------------------------------------------------------

class A2AGateway:
    """Agent-to-Agent gateway for AIMart.

    Manages a simple in-memory registry of agent endpoints and provides
    methods for inter-agent message routing and negotiation.
    """

    def __init__(self) -> None:
        self._registry: dict[str, AgentEndpoint] = {}
        self._negotiations: dict[str, NegotiationSession] = {}

    # -- Registry ------------------------------------------------------------

    def register_agent_endpoint(
        self,
        agent_id: str,
        capabilities: list[str],
        endpoint_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentEndpoint:
        """Register an agent for A2A communication.

        If the agent is already registered its entry is updated.

        Parameters
        ----------
        agent_id:
            Unique identifier of the agent.
        capabilities:
            List of capability tags this agent exposes (e.g.
            ``["pricing", "dispute_resolution"]``).
        endpoint_url:
            Optional URL where the agent can receive A2A messages.
        metadata:
            Arbitrary metadata to store alongside the registration.
        """
        entry = AgentEndpoint(
            agent_id=agent_id,
            capabilities=capabilities,
            endpoint_url=endpoint_url,
            metadata=metadata or {},
        )
        self._registry[agent_id] = entry
        logger.info(
            "a2a.agent_registered",
            agent_id=agent_id,
            capabilities=capabilities,
        )
        return entry

    def get_agent(self, agent_id: str) -> AgentEndpoint | None:
        """Look up a registered agent by ID."""
        return self._registry.get(agent_id)

    def list_agents(self, capability: str | None = None) -> list[AgentEndpoint]:
        """List all registered agents, optionally filtered by capability."""
        agents = list(self._registry.values())
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        return agents

    # -- Message routing -----------------------------------------------------

    async def handle_agent_message(
        self,
        sender_agent_id: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """Route a message from one agent to its intended target.

        Parameters
        ----------
        sender_agent_id:
            The agent sending the message.
        message:
            The A2A message payload.  Must contain a ``target_agent_id`` key
            and a ``payload`` key.

        Returns
        -------
        dict
            The target agent's response, or an error dict if routing fails.
        """
        target_id = message.get("target_agent_id")
        if not target_id:
            logger.warning("a2a.missing_target", sender=sender_agent_id)
            return {"error": "message must include 'target_agent_id'"}

        sender = self._registry.get(sender_agent_id)
        target = self._registry.get(target_id)

        if sender is None:
            logger.warning("a2a.unknown_sender", sender=sender_agent_id)
            return {"error": f"sender agent '{sender_agent_id}' not registered"}

        if target is None:
            logger.warning("a2a.unknown_target", target=target_id)
            return {"error": f"target agent '{target_id}' not registered"}

        logger.info(
            "a2a.message_routed",
            sender=sender_agent_id,
            target=target_id,
            msg_type=message.get("type", "unknown"),
        )

        # In production this would POST to target.endpoint_url or enqueue
        # a Kafka message.  For now we return a placeholder acknowledgment.
        return {
            "status": "delivered",
            "sender": sender_agent_id,
            "target": target_id,
            "acknowledged": True,
        }

    # -- Negotiation ---------------------------------------------------------

    async def negotiate(
        self,
        agent_a: str,
        agent_b: str,
        topic: str,
        initial_offer: dict[str, Any] | None = None,
    ) -> NegotiationSession:
        """Facilitate a negotiation between two agents.

        Typical use-cases include price negotiation and dispute resolution.
        The method creates a negotiation session and records the initial
        offer (if provided).

        Parameters
        ----------
        agent_a:
            The agent initiating the negotiation (usually the buyer).
        agent_b:
            The counter-party agent (usually the seller/provider).
        topic:
            A human/machine-readable topic string, e.g. ``"pricing"`` or
            ``"dispute:order-123"``.
        initial_offer:
            Optional first offer payload from *agent_a*.

        Returns
        -------
        NegotiationSession
            The newly created negotiation session.
        """
        for aid in (agent_a, agent_b):
            if aid not in self._registry:
                msg = f"agent '{aid}' not registered for A2A"
                logger.error("a2a.negotiate_unknown_agent", agent=aid)
                raise ValueError(msg)

        session = NegotiationSession(
            session_id=str(uuid.uuid4()),
            agent_a=agent_a,
            agent_b=agent_b,
            topic=topic,
        )

        if initial_offer:
            session.rounds.append({
                "round": 1,
                "from": agent_a,
                "offer": initial_offer,
                "timestamp": time.time(),
            })

        self._negotiations[session.session_id] = session
        logger.info(
            "a2a.negotiation_started",
            session_id=session.session_id,
            agent_a=agent_a,
            agent_b=agent_b,
            topic=topic,
        )
        return session

    def get_negotiation(self, session_id: str) -> NegotiationSession | None:
        """Retrieve an active negotiation by session ID."""
        return self._negotiations.get(session_id)

    async def add_negotiation_round(
        self,
        session_id: str,
        from_agent_id: str,
        offer: dict[str, Any],
    ) -> NegotiationSession:
        """Append a round to an active negotiation.

        If the offer contains ``"accepted": True`` the negotiation is
        automatically marked as settled.
        """
        session = self._negotiations.get(session_id)
        if session is None:
            msg = f"negotiation session '{session_id}' not found"
            raise ValueError(msg)

        if session.status != "active":
            msg = f"negotiation '{session_id}' is not active (status={session.status})"
            raise ValueError(msg)

        round_num = len(session.rounds) + 1
        session.rounds.append({
            "round": round_num,
            "from": from_agent_id,
            "offer": offer,
            "timestamp": time.time(),
        })

        if offer.get("accepted"):
            session.status = "settled"
            session.settled_at = time.time()
            session.result = offer
            logger.info("a2a.negotiation_settled", session_id=session_id)
        else:
            logger.info(
                "a2a.negotiation_round",
                session_id=session_id,
                round=round_num,
                from_agent=from_agent_id,
            )

        return session
