# Architecture Overview

## High‑Level Components

| Component | Purpose | Key Files |
|-----------|---------|----------|
| **CLI (`cli.py`)** | Entry point for the competition. Parses commands, loads cases, runs the workflow, validates outputs, and builds the submission zip. | `src/student_agent/cli.py` |
| **Workflow (`workflow.py`)** | Orchestrates the deterministic DAG for each case. Calls the specialist agents, runs them in parallel, aggregates results, and emits trace events. | `src/student_agent/workflow.py` |
| **Specialist Agents (`agents.py`)** | Deterministic agents for Entity, Order, Shipment, Payment, and Policy. Each agent calls a specific MCP tool via `EvidenceGateway` and returns a schema‑compliant dict. | `src/student_agent/agents.py` |
| **Conflict Resolver (`conflict_resolver.py`)** | Detects simple inconsistencies (order‑id mismatches) between the specialist agents and collects all evidence references. | `src/student_agent/conflict_resolver.py` |
| **MCP Gateway (`mcp_gateway.py`)** | Wraps the MCP client, normalises error handling, validates evidence against the contract schemas, and returns parsed JSON evidence. | `src/student_agent/mcp_gateway.py` |
| **Trace Writer (`trace.py`)** | Emits observable events (`case_received`, `task_assigned`, `handoff`, …) to a JSON‑L file for later validation and debugging. | `src/student_agent/trace.py` |
| **Contracts (`contracts.py`)** | Loads and validates JSON‑Schema contracts for inputs, outputs, evidence, and trace events. | `src/student_agent/contracts.py` |
| **Submission (`submission.py`)** | Packages the `outputs/` and `trace/` directories into a zip ready for submission. | `src/student_agent/submission.py` |

## Data Flow (Day 3 DAG)

```mermaid
flowchart TD
    A[Case Input] --> B[EntityAgent]
    B --> C[OrderAgent]
    B --> D[ShipmentAgent]
    B --> E[PaymentAgent]
    B --> F[PolicyAgent]
    C & D & E & F --> G[ConflictResolver]
    G --> H[Final Output]
    H --> I[Trace (handoff)]
```

1. **EntityAgent** resolves the order IDs for the case.
2. **OrderAgent** fetches order details.
3. **ShipmentAgent**, **PaymentAgent**, **PolicyAgent** run concurrently because they are independent.
4. **ConflictResolver** (Day 4) checks for mismatches and assembles a unified list of evidence refs.
5. The workflow aggregates all partial results into the final output JSON that matches `l3b-output-v2.schema.json`.

## Running All 100 Cases

A convenience script `run_all_cases.py` is provided at the repository root. It sets the repository root on `sys.path` and invokes the CLI’s internal `_run` coroutine, which processes every case in `inputs/` and writes the results to `outputs/` while emitting a full trace.

## Extensibility

- **Day 4** adds deterministic conflict resolution without changing the DAG.
- **Day 5** will replace the deterministic agents with LLM‑backed agents and introduce verification logic.
- The architecture isolates MCP communication, tracing, and contract validation, making it straightforward to swap implementations.

---
*This document is intended for reviewers and future developers to understand the system layout and the responsibilities of each module.*
