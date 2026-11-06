# Nora — Member 2: Case State & Tools

This package implements **Member 2 only**: validated per-call case state, tool orchestration, mock alerts, and an optional in-process event bus for Member 3's dashboard. `triage.py` is an **unchanged copy of Member 1's exact triage engine** for standalone testing; when merging, keep one canonical `triage.py` from Member 1.

## Run

```bash
uv run --with pytest python -m pytest -q
```

No LiveKit/API keys required to test this module.

## Interface contract for Member 4

Create a **new `CaseTools()` instance per caller/session**. Never share a global `CaseTools` across concurrent calls.

```python
from tools import CaseTools
backend = CaseTools()
backend.update_case('substance', 'raisins')
backend.update_case('breathing_normal', True)
result = backend.assess_case()
alert = backend.alert_on_call_vet('Caller reports raisins ingestion')
```

- `update_case(field: str, value) -> dict`: validates and saves a field, returns full state snapshot, invalidates stale assessment when value changes.
- `assess_case() -> dict`: calls Member 1 `assess_ingestion(case)`; returns `label`, `reason`, `next_step`, `rule_id`.
- `alert_on_call_vet(summary: str) -> dict`: mock only; **no actual SMS, no veterinary dispatch**.
- `get_case() -> dict`: defensive copy of current state.

Supported fields: `substance`, `amount`, `dog_weight_kg`, `minutes_since`, `symptoms`, `callback`, `breathing_normal`.

`breathing_normal` requires a real bool (`True`/`False`), not a string. `symptoms` takes a list of strings or one string. `minutes_since` is a whole number. `callback` is normalized to digits.

## Integration with Member 3

```python
from events import DEFAULT_BUS
DEFAULT_BUS.subscribe(lambda event: print(event))
```

Event types: `case_updated`, `assessment`, `mock_alert`. `case_updated` emits only field name/revision by default, not the raw callback number. **This in-memory bus works only within the same Python process.** For a dashboard in another process, Member 3/4 must implement a transport such as HTTP/WebSocket or LiveKit data messages. The `EventBus` intentionally doesn't implement a network server.

## Git merge steps

1. Member 1 owns canonical `triage.py`.
2. Member 2 contributes `case_state.py`, `tools.py`, `events.py` and `tests/test_case_tools.py`.
3. Member 4 wraps `CaseTools` methods with the official starter's LiveKit function tools. `agent_tool_adapter_example.py` is pseudointegration, **not a runnable LiveKit agent**.
4. Member 3 subscribes to events or uses a network bridge. Avoid showing personal callback numbers publicly on the dashboard.
5. Run all tests from the repo root. Test an interruption and a changed-substance call end to end.

## Safety

This is a demo case-management system, **not clinical veterinary guidance**. It does not diagnose, calculate toxic doses, prescribe home treatment, or send real alerts. Member 1's simple keyword engine may misinterpret negated symptoms; the voice agent must clarify ambiguity. Always direct suspected ingestion to a veterinary professional, and seek emergency veterinary help for serious symptoms. No claim of guaranteed correctness.
