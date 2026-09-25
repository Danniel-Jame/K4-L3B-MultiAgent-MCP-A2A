"""Deterministic specialist agents for Day 2.
These agents are intentionally simple and do not perform any LLM calls. They each
receive the `case` dict and an `EvidenceGateway` instance for MCP tool calls.
All agents emit trace events via the provided `TraceWriter`.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .mcp_gateway import EvidenceGateway
from .trace import TraceWriter


async def _emit(trace: TraceWriter, case_id: str, event_type: str, actor: str, **kwargs: Any) -> None:
    """Helper to emit a trace event.

    Args:
        trace: TraceWriter instance.
        case_id: Identifier of the case.
        event_type: Type of the event (e.g., "task_assigned").
        actor: Name of the component emitting the event.
        **kwargs: Additional fields forwarded to ``TraceWriter.emit``.
    """
    trace.emit(
        case_id=case_id,
        event_type=event_type,
        actor=actor,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Entity resolution agent
# ---------------------------------------------------------------------------

async def entity_agent(
    case: Dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> Dict[str, Any]:
    """Resolve the order(s) that belong to the case.

    This deterministic implementation simply treats every candidate order ID as a
    resolved order. In a real solution the LLM would decide which candidate(s)
    are correct.
    """
    case_id = case.get("case_id", "unknown")
    await _emit(trace, case_id, "task_assigned", "entity_agent")

    # The input case contains a ``candidate_order_ids`` field (list of strings).
    # We mark all of them as resolved for the deterministic baseline.
    resolved = case.get("candidate_order_ids", [])
    result = {
        "status": "resolved",
        "resolved_order_ids": resolved,
        "rejected_candidates": [],
        "confidence": 1.0,
    }
    await _emit(
        trace,
        case_id,
        "handoff",
        "entity_agent",
        target="order_agent",
        attributes=result,
    )
    return result


# ---------------------------------------------------------------------------
# Order information agent
# ---------------------------------------------------------------------------

async def order_agent(
    case: Dict[str, Any],
    gateway: EvidenceGateway,
    trace: TraceWriter,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch order details via the ``get_order`` MCP tool.

    The function returns the raw ``evidence_ref`` together with a minimal
    placeholder payload required by later stages.
    """
    case_id = case.get("case_id", "unknown")
    await _emit(trace, case_id, "task_assigned", "order_agent")

    if not order_id:
        # No order to fetch – return empty placeholders.
        return {"evidence_ref": None, "order_data": {}}

    # Call the deterministic MCP tool.
    tool_result = await gateway.call(
        "get_order", case_id=case_id, order_id=order_id
    )
    # ``tool_result`` is expected to be a dict with ``evidence_ref`` and ``data``.
    evidence_ref = tool_result.get("evidence_ref")
    data = tool_result.get("data", {})
    await _emit(
        trace,
        case_id,
        "tool_result_consumed",
        "order_agent",
        tool_name="get_order",
        evidence_refs=[evidence_ref] if evidence_ref else None,
    )
    return {"evidence_ref": evidence_ref, "order_data": data}


# ---------------------------------------------------------------------------
# Shipment analysis agent
# ---------------------------------------------------------------------------

async def shipment_agent(
    case: Dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> Dict[str, Any]:
    """Obtain shipment summary and produce a deterministic verdict.

    For the baseline we always answer ``on_time`` and set ``timeline_complete``
    to ``True``.
    """
    case_id = case.get("case_id", "unknown")
    await _emit(trace, case_id, "task_assigned", "shipment_agent")

    result = await gateway.call("get_shipment_summary", case_id=case_id)
    evidence_ref = result.get("evidence_ref")
    await _emit(
        trace,
        case_id,
        "tool_result_consumed",
        "shipment_agent",
        tool_name="get_shipment_summary",
        evidence_refs=[evidence_ref] if evidence_ref else None,
    )
    payload = {
        "verdict": "on_time",
        "late_seller_ids": [],
        "timeline_complete": True,
    }
    return {"evidence_ref": evidence_ref, "analysis": payload}


# ---------------------------------------------------------------------------
# Payment analysis agent
# ---------------------------------------------------------------------------

async def payment_agent(
    case: Dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> Dict[str, Any]:
    """Fetch payment details and produce a deterministic reconciliation verdict.
    """
    case_id = case.get("case_id", "unknown")
    await _emit(trace, case_id, "task_assigned", "payment_agent")

    result = await gateway.call("get_order_payments", case_id=case_id)
    evidence_ref = result.get("evidence_ref")
    await _emit(
        trace,
        case_id,
        "tool_result_consumed",
        "payment_agent",
        tool_name="get_order_payments",
        evidence_refs=[evidence_ref] if evidence_ref else None,
    )
    payload = {
        "verdict": "reconciled",
        "captured_total_brl": 0,
        "refunded_total_brl": 0,
        "refundable_total_brl": 0,
    }
    return {"evidence_ref": evidence_ref, "analysis": payload}


# ---------------------------------------------------------------------------
# Policy agent
# ---------------------------------------------------------------------------

async def policy_agent(
    case: Dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> Dict[str, Any]:
    """Retrieve the relevant policy version.
    The deterministic implementation simply forwards the policy version from the
    case and returns an empty dict for the policy content.
    """
    case_id = case.get("case_id", "unknown")
    await _emit(trace, case_id, "task_assigned", "policy_agent")

    policy_version = case.get("policy_version", "default")
    result = await gateway.call(
        "get_policy", case_id=case_id, policy_version=policy_version
    )
    evidence_ref = result.get("evidence_ref")
    await _emit(
        trace,
        case_id,
        "tool_result_consumed",
        "policy_agent",
        tool_name="get_policy",
        evidence_refs=[evidence_ref] if evidence_ref else None,
    )
    payload = {"policy_version": policy_version, "details": result.get("data", {})}
    return {"evidence_ref": evidence_ref, "policy": payload}


# ---------------------------------------------------------------------------
# Utility to collect evidence refs from agent results
# ---------------------------------------------------------------------------

def _collect_refs(*results: Dict[str, Any]) -> List[str]:
    refs: List[str] = []
    for r in results:
        ref = r.get("evidence_ref")
        if ref:
            refs.append(ref)
    return refs


# ---------------------------------------------------------------------------
# Coordinator (workflow) – implemented in ``workflow.py``
# ---------------------------------------------------------------------------
# The ``solve_case`` function in ``workflow.py`` imports the agents defined above.
# This file only contains the agents; the orchestration lives in the companion
# ``workflow.py`` file.
