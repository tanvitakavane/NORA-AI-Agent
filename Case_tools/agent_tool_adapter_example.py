"""Illustrative Member 4 integration. Adapt to the event's official LiveKit starter.

DO NOT replace the event starter's agent entrypoint with this file.
"""
from tools import CaseTools

# Instantiate CaseTools() inside the LiveKit session/agent constructor, once per call.
# Tool schemas in the official starter may require explicit typed parameters.

class NoraToolBridge:
    def __init__(self):
        self.backend = CaseTools()

    def update_case(self, field: str, value: str):
        # Member 4 should convert typed values (e.g. breathing_normal: bool,
        # dog_weight_kg: float, symptoms: list[str]) before calling update_case.
        return self.backend.update_case(field, value)

    def assess_ingestion(self):
        return self.backend.assess_case()

    def alert_on_call_vet(self, summary: str):
        return self.backend.alert_on_call_vet(summary)
