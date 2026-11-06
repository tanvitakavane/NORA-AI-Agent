# Member 1 — Nora Backend & Triage Engine

This is a **drop-in replacement** for `triage.py` in the shared Nora starter. It uses **only Python standard library** at runtime. Tests use pytest.

## Ownership
- `triage.py`: pure Python assessment function, no network, no LLM, no LiveKit dependencies.
- `tests/test_triage.py`: routing, precedence, edge-case and output-contract tests.
- Do **not** edit Member 2's `case_state.py` or `tools.py` or Member 4's `agent.py`.

## Contract for Member 2 and Member 4

```python
from triage import assess_ingestion
result = assess_ingestion({
    'substance': 'raisins',
    'amount': 'a handful',
    'dog_weight_kg': 14,
    'minutes_since': 20,
    'symptoms': [],
    'breathing_normal': True,
})
# {'label': 'CONTACT_VET_NOW', 'reason': '...',
#  'next_step': '...', 'rule_id': 'KNOWN_CONCERN'}
```

Input: dictionary; missing keys allowed. Output: always exactly four string keys: `label`, `reason`, `next_step`, `rule_id`.

Labels: `EMERGENCY`, `CONTACT_VET_NOW`, `NEEDS_MORE_INFORMATION`. No `MONITOR_AT_HOME` clearance.

Member 2 should call `assess_ingestion(self.case.snapshot())` **after every material correction** and invalidate previous assessments. Member 4 should speak the `next_step` naturally and must not claim the rules provide medical diagnosis.

## Run tests

From this folder:

```bash
uv run --with pytest python -m pytest -q
```

Or if pytest is already installed:

```bash
python -m pytest -q
```

## Merge into shared repo

1. Copy `triage.py` into the shared repo root, replacing the old version.
2. Copy `tests/test_triage.py` into the shared repo's `tests/` folder (review any existing test cases before replacing).
3. Run `uv run --with pytest python -m pytest -q` from the repo root.
4. Ask Member 2 to run `CaseTools().assess_case()` to confirm the return contract.
5. Ask Member 4 to test one emergency, one unknown ingestion, and a correction on the actual voice agent.

## Safety and demo limits

- **Not veterinary advice.** These are intentionally conservative demonstration routing rules, not validated clinical triage or toxicology thresholds.
- Do not give vomiting instructions, dose calculations, or assurances of safety.
- Emergency symptoms trigger emergency veterinary routing; uncertain ingestions route to a veterinarian/poison-control service.
- Keyword matching can miss slang, negation (e.g. 'not having a seizure'), and mis-transcribed words. The voice agent must ask clarification questions and avoid treating this engine as definitive. Do not claim it is impossible to hallucinate.
- This module does not send messages, book care, or validate phone numbers. Those are separate team responsibilities.
