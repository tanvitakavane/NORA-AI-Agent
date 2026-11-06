"""Validated, per-call case state. No network calls or clinical decisions."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from copy import deepcopy
import re
from typing import Any

ALLOWED = frozenset({'substance','amount','dog_weight_kg','minutes_since','symptoms','callback','breathing_normal'})

def _clean(field_name: str, value: Any) -> Any:
    if value is None:
        return None
    if field_name in {'substance','amount'}:
        if not isinstance(value, str) or not value.strip() or len(value) > 300:
            raise ValueError(f'{field_name} must be a nonempty string of at most 300 characters')
        return value.strip()
    if field_name == 'callback':
        if not isinstance(value, str):
            raise ValueError('callback must be a string')
        digits = re.sub(r'\D','',value)
        if not 7 <= len(digits) <= 15:
            raise ValueError('callback must contain 7 to 15 digits')
        return digits
    if field_name == 'dog_weight_kg':
        if isinstance(value, bool):
            raise ValueError('weight must be numeric')
        try:
            v = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('weight must be numeric') from None
        if not 0 < v <= 200:
            raise ValueError('weight must be between 0 and 200 kg')
        return v
    if field_name == 'minutes_since':
        if isinstance(value, bool) or isinstance(value, float) and not value.is_integer():
            raise ValueError('minutes_since must be a whole number')
        try:
            v = int(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('minutes_since must be a whole number') from None
        if not 0 <= v <= 525600:
            raise ValueError('minutes_since out of range')
        return v
    if field_name == 'breathing_normal':
        if type(value) is not bool:
            raise ValueError('breathing_normal must be true, false, or null')
        return value
    if field_name == 'symptoms':
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or len(value) > 20:
            raise ValueError('symptoms must be a list of at most 20 strings')
        if not all(isinstance(x, str) and 0 < len(x.strip()) <= 200 for x in value):
            raise ValueError('each symptom must be a nonempty string up to 200 characters')
        return list(dict.fromkeys(x.strip() for x in value))
    raise ValueError(f'Unsupported field: {field_name}')

@dataclass
class CaseState:
    substance: str | None = None
    amount: str | None = None
    dog_weight_kg: float | None = None
    minutes_since: int | None = None
    symptoms: list[str] = field(default_factory=list)
    callback: str | None = None
    breathing_normal: bool | None = None
    assessment: dict | None = None
    history: list[dict] = field(default_factory=list)
    revision: int = 0

    def update(self, field_name: str, value: Any) -> dict:
        if field_name not in ALLOWED:
            raise ValueError(f'Unsupported field: {field_name}')
        new_value = _clean(field_name, value)
        old_value = deepcopy(getattr(self, field_name))
        if old_value == new_value:
            return self.snapshot()
        setattr(self, field_name, new_value)
        self.revision += 1
        self.assessment = None  # A correction invalidates the previous assessment.
        self.history.append({'revision': self.revision, 'field': field_name,
                             'previous': old_value, 'new': deepcopy(new_value),
                             'at': datetime.now(timezone.utc).isoformat()})
        return self.snapshot()

    def snapshot(self) -> dict:
        return deepcopy(asdict(self))

    def triage_input(self) -> dict:
        return {key: deepcopy(getattr(self, key)) for key in ALLOWED}
