import asyncio
from typing import Any, Dict, List, Optional

from .mcp_gateway import EvidenceGateway
from .trace import TraceWriter
from .agents import (
    entity_agent,
    order_agent,
    shipment_agent,
    payment_agent,
    policy_agent,
)


async def solve_case(
    case: Dict[str, Any],
    gateway: EvidenceGateway,
    trace: TraceWriter,
) -> Dict[str, Any]:
    """Day 3 DAG orchestration.

    1️⃣ Entity resolution – determines which order(s) belong to the case.
    2️⃣ Order details – fetched via ``get_order``.
    3️⃣ Shipment, payment, and policy analysis – run **concurrently** because they are independent.
    4️⃣ Aggregate all partial results into the final output matching the L3B schema.
    """

    # ---- Entity resolution -------------------------------------------------
    entity_res = await entity_agent(case, gateway, trace)
    # ``entity_res`` follows the ``entity_resolution`` schema section.
    resolved_ids: List[str] = entity_res.get("resolved_order_ids", [])
    resolved_order_id: Optional[str] = resolved_ids[0] if resolved_ids else None

    # ---- Order details -----------------------------------------------------
    order_res = await order_agent(case, gateway, trace, order_id=resolved_order_id)

    # ---- Parallel deterministic agents --------------------------------------
    shipment_task = shipment_agent(case, gateway, trace)
    payment_task = payment_agent(case, gateway, trace)
    policy_task = policy_agent(case, gateway, trace)
    shipment_res, payment_res, policy_res = await asyncio.gather(
        shipment_task, payment_task, policy_task
    )

    # ---- Assemble final output --------------------------------------------
    final_output: Dict[str, Any] = {
        "entity_resolution": entity_res,
        "order_details": order_res.get("order_data"),
        "shipment_analysis": shipment_res.get("analysis"),
        "payment_analysis": payment_res.get("analysis"),
        "policy_analysis": policy_res.get("policy"),
        # The remaining top‑level fields required by the schema will be filled
        # later (assessment, affected_entities, etc.). For Day 3 we provide the
        # deterministic core sections.
    }

    # Emit a final handoff event so the trace reflects completion of the DAG.
    trace.emit(
        case_id=case.get("case_id", "unknown"),
        event_type="handoff",
        actor="workflow",
        target="final_output",
    )

    return final_output
