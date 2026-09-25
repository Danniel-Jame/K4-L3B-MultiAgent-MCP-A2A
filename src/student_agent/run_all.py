import asyncio
import json
from pathlib import Path

from .cases import load_case_set
from .config import Settings
from .contracts import Contracts
from .trace import TraceWriter
from .workflow import solve_case

# Minimal mock gateway that returns empty evidence structures
class MockGateway:
    async def list_tools(self):
        return []
    async def call(self, tool_name: str, *, case_id: str, **arguments):
        return {}

async def main():
    root = Path('.').resolve()
    settings = Settings.load(root)
    case_set = load_case_set(root)
    contracts = Contracts(root / 'contracts' / 'schemas')
    output_root = root / 'outputs'
    trace_path = root / 'traces' / 'trace.jsonl'
    output_root.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace = TraceWriter(trace_path, contracts)
    gateway = MockGateway()
    for case_id, case in case_set.cases.items():
        trace.emit(case_id=case_id, event_type='case_received', actor='coordinator')
        output = await solve_case(case, gateway, trace)
        output.setdefault('case_id', case_id)
        target = output_root / f"{case_id}.json"
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
        trace.emit(case_id=case_id, event_type='case_finalized', actor='coordinator')

if __name__ == '__main__':
    asyncio.run(main())
