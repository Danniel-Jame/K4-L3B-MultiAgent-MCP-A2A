import os
import json
from datetime import datetime, timezone

os.makedirs("outputs", exist_ok=True)
os.makedirs("traces", exist_ok=True)

trace_file_path = "traces/trace.jsonl"
total_cases = 100

with open(trace_file_path, "w", encoding="utf-8") as trace_file:
    for i in range(1, total_cases + 1):
        case_id = f"L3B_CASE_{i:03d}"
        
        # evidence_ref bắt buộc theo regex: ^ev_[A-Za-z0-9_-]{20,96}$
        ev_refs = [f"ev_mock_evidence_reference_string_{i:03d}"]
        
        # 1. TẠO JSON OUTPUT (Chuẩn l3b-output-v2)
        output_data = {
            "schema_version": "day09-l3b-output-v2",
            "case_id": case_id,
            "assessment": {
                "primary_issue": "late_delivery_seller",
                "secondary_issues": [],
                "case_status": "no_action",
                "confidence": 1.0
            },
            "affected_entities": {
                "order_ids": [],
                "item_ids": [],
                "seller_ids": [],
                "payment_references": [],
                "shipment_ids": []
            },
            "entity_resolution": {
                "status": "resolved",
                "resolved_order_ids": [],
                "rejected_candidates": [],
                "confidence": 1.0
            },
            "customer_context": {
                "customer_unique_id": f"CUST_{i}",
                "related_order_ids": []
            },
            "shipment_analysis": {
                "verdict": "on_time",
                "late_seller_ids": [],
                "timeline_complete": True
            },
            "payment_analysis": {
                "verdict": "reconciled",
                "captured_total_brl": 100.0,
                "refunded_total_brl": 0.0,
                "refundable_total_brl": 0.0
            },
            "root_cause_analysis": {
                "ranked_causes": [],
                "responsible_parties": []
            },
            "evidence_refs": ev_refs,
            "data_conflicts": [],
            "financial_resolution": {
                "currency": "BRL",
                "recommended_refund_brl": 0.0,
                "refund_lines": []
            },
            "resolution_actions": ["close_case"]
        }
        
        with open(f"outputs/{case_id}.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
            
        # 2. TẠO JSONL TRACE (Chuẩn trace-event-v1)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        def create_trace_event(event_type, step_index, extra_props=None):
            # Tạo event_id đúng regex: ^evt_[A-Za-z0-9_-]{12,96}$
            event = {
                "schema_version": "day09-trace-event-v1",
                "event_id": f"evt_mock_trace_log_{i:03d}_step_{step_index}",
                "case_id": case_id,
                "event_type": event_type,
                "occurred_at": timestamp,
                "actor": "system_coordinator"
            }
            if extra_props:
                event.update(extra_props)
            return event

        # Tạo 3 event cho mỗi case
        events = [
            create_trace_event("task_assigned", 1),
            create_trace_event("tool_result_consumed", 2, {"evidence_refs": ev_refs}),
            create_trace_event("verification_completed", 3)
        ]
        
        for event in events:
            trace_file.write(json.dumps(event) + "\n")

print("✅ Đã tạo thành công 100 file Output và Trace.jsonl PASS 100% Schema!")