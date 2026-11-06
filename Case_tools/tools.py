"""Pure-Python agent tool adapter. Member 4 wraps these with LiveKit @function_tool."""
from copy import deepcopy
from uuid import uuid4
from case_state import CaseState
from events import DEFAULT_BUS, EventBus
from triage import assess_ingestion

class CaseTools:
    def __init__(self, case_id: str | None = None, bus: EventBus | None = None):
        # IMPORTANT: instantiate once per phone call, never globally for all callers.
        self.case_id = case_id or uuid4().hex[:12]
        self.case = CaseState()
        self.bus = bus if bus is not None else DEFAULT_BUS
        self._alerts: list[dict] = []

    def update_case(self, field: str, value) -> dict:
        """Validated update; a correction automatically invalidates prior assessment."""
        before = self.case.revision
        snapshot = self.case.update(field, value)
        if self.case.revision != before:
            # Do not broadcast phone numbers or sensitive raw case values by default.
            self.bus.publish('case_updated', {'field': field, 'revision': self.case.revision,
                                               'assessment_stale': True}, self.case_id)
        return snapshot

    def assess_case(self) -> dict:
        """Always use Member 1's deterministic triage engine; no LLM decision."""
        result = assess_ingestion(self.case.triage_input())
        required = {'label','reason','next_step','rule_id'}
        if not isinstance(result, dict) or not required.issubset(result):
            raise RuntimeError('Unexpected triage engine output contract')
        self.case.assessment = deepcopy(result)
        self.bus.publish('assessment', {'revision': self.case.revision, **result}, self.case_id)
        return deepcopy(result)

    def alert_on_call_vet(self, summary: str) -> dict:
        """Creates a MOCK notification only; no SMS or veterinary contact occurs."""
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 1000:
            raise ValueError('summary must be 1-1000 characters')
        # Reassess if facts changed; refuse to imply a real message was delivered.
        result = self.assess_case() if self.case.assessment is None else deepcopy(self.case.assessment)
        alert = {'status': 'MOCK_ALERT_CREATED', 'alert_id': f'MOCK-{uuid4().hex[:8]}',
                 'case_id': self.case_id, 'triage_label': result['label'],
                 'summary': summary.strip(), 'delivered': False}
        self._alerts.append(deepcopy(alert))
        self.bus.publish('mock_alert', {'alert_id': alert['alert_id'], 'status': alert['status'],
                                        'triage_label': alert['triage_label']}, self.case_id)
        return deepcopy(alert)

    def get_case(self) -> dict:
        return self.case.snapshot()

    def get_alerts(self) -> list[dict]:
        return deepcopy(self._alerts)
