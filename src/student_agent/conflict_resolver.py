"""Deterministic conflict resolver for Day 4.
It examines the outputs of the deterministic agents and produces a list of
conflicts (if any) together with a consolidated list of evidence references.
The logic is intentionally simple – it only checks that the order IDs reported
by the various agents are consistent.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ConflictResolver:
    """Resolve data conflicts between specialist-agent results.

    The resolver receives the *raw* dictionaries produced by the agents (the
    values returned from ``order_agent``, ``shipment_agent``, ``payment_agent``
    and ``policy_agent``). It returns a dictionary containing:
    * ``data_conflicts`` – a list of conflict objects.
    * ``evidence_refs`` – a flat list of all evidence references seen.
    """

    @staticmethod
    def resolve(
        order_res: Dict[str, Any],
        shipment_res: Dict[str, Any],
        payment_res: Dict[str, Any],
        policy_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        conflicts: List[Dict[str, Any]] = []
        evidence_refs: List[str] = []

        # Helper to push evidence refs if present
        def add_ref(part: Dict[str, Any]):
            ev = part.get("evidence_ref")
            if ev:
                evidence_refs.append(ev)

        for part in (order_res, shipment_res, payment_res, policy_res):
            add_ref(part)

        # Simple deterministic check: order_id consistency across agents.
        # The agents we wrote expose the order id under different keys; we look
        # for a common ``order_id`` field in each result.
        order_id = order_res.get("order_id")
        shipment_order_id = shipment_res.get("order_id")
        payment_order_id = payment_res.get("order_id")

        def report_mismatch(agent_a: str, id_a: Optional[str], agent_b: str, id_b: Optional[str]):
            conflicts.append(
                {
                    "type": "order_id_mismatch",
                    "detail": f"{agent_a} reports {id_a!r} while {agent_b} reports {id_b!r}",
                    "agents": [agent_a, agent_b],
                }
            )

        if order_id and shipment_order_id and order_id != shipment_order_id:
            report_mismatch("order_agent", order_id, "shipment_agent", shipment_order_id)
        if order_id and payment_order_id and order_id != payment_order_id:
            report_mismatch("order_agent", order_id, "payment_agent", payment_order_id)

        return {"data_conflicts": conflicts, "evidence_refs": evidence_refs}
