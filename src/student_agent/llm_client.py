"""llm_client.py

Utility module to call an LLM. In Day 4 the conflict resolver may invoke an LLM to
reason about contradictory evidence. For rapid development we provide a simple
async ``call_llm`` function that supports a ``mock`` mode returning a deterministic
payload that matches a supplied JSON schema.
"""

import json
from typing import Any, Dict


async def call_llm(prompt: str, schema: Dict[str, Any] | None = None, *, mock: bool = False) -> Dict[str, Any]:
    """Call an LLM and obtain JSON output.

    Parameters
    ----------
    prompt: str
        The prompt sent to the model.
    schema: dict | None
        Optional JSON schema describing the expected output. When ``mock`` is True a
        deterministic dummy payload is generated based on the schema.
    mock: bool, default False
        If True, return a dummy payload without contacting any external service.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    if mock:
        # Generate a minimal object that satisfies the schema (if provided).
        if schema and isinstance(schema, dict) and "properties" in schema:
            dummy: Dict[str, Any] = {}
            for key, prop in schema["properties"].items():
                typ = prop.get("type", "string")
                if isinstance(typ, list):
                    typ = typ[0]
                if typ == "string":
                    dummy[key] = f"dummy_{key}"
                elif typ == "number":
                    dummy[key] = 0
                elif typ == "boolean":
                    dummy[key] = False
                elif typ == "array":
                    dummy[key] = []
                else:
                    dummy[key] = None
            return dummy
        return {"dummy": "value"}

    # Real LLM integration point – raise to remind developers to plug in a provider.
    raise NotImplementedError("Real LLM integration not implemented. Use mock=True for deterministic behavior.")
