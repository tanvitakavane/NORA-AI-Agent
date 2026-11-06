"""Nora demo routing engine. NOT veterinary medical advice or a toxicity calculator.

Contract: assess_ingestion(case: dict) -> dict with label, reason, next_step, rule_id.
No external dependencies. Never returns a home-monitoring clearance.
"""
from dataclasses import asdict, dataclass
import re
from typing import Any

EMERGENCY = 'EMERGENCY'
CONTACT_VET_NOW = 'CONTACT_VET_NOW'
NEEDS_MORE_INFORMATION = 'NEEDS_MORE_INFORMATION'

# Example routing keywords, not a complete veterinary toxicology database.
RED_FLAG_PHRASES = {
    'seizure': ('seizure', 'seizing', 'convulsion', 'convulsing'),
    'collapse': ('collapse', 'collapsed', 'collapsing', 'passed out', 'unresponsive', 'unconscious'),
    'breathing_difficulty': ('trouble breathing', 'difficulty breathing', 'cannot breathe',
                             "can't breathe", 'struggling to breathe', 'gasping'),
    'severe_bleeding': ('severe bleeding', 'bleeding heavily'),
}
CONCERN_PHRASES = {
    'xylitol': ('xylitol', 'birch sugar'),
    'grapes_or_raisins': ('grape', 'grapes', 'raisin', 'raisins'),
    'antifreeze': ('antifreeze', 'ethylene glycol'),
    'rodenticide': ('rat poison', 'mouse poison', 'rodenticide'),
    'human_medication': ('ibuprofen', 'advil', 'motrin', 'tylenol', 'acetaminophen',
                         'paracetamol', 'human medication', 'human pills'),
    'chocolate': ('chocolate', 'cocoa'),
}

@dataclass(frozen=True)
class Assessment:
    label: str
    reason: str
    next_step: str
    rule_id: str


def _normalize(value: Any) -> str:
    """Normalize common punctuation/spacing without guessing substance identity."""
    if value is None:
        return ''
    text = str(value).casefold().replace('’', "'")
    return re.sub(r'\s+', ' ', text).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    """Whole phrase matching avoids 'grape' matching 'grapefruit'."""
    return bool(re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text))


def _matches(text: str, patterns: dict[str, tuple[str, ...]]) -> str | None:
    for category, phrases in patterns.items():
        if any(_contains_phrase(text, p) for p in phrases):
            return category
    return None


def _symptom_text(raw: Any) -> str:
    if raw is None:
        return ''
    if isinstance(raw, str):
        return _normalize(raw)
    if isinstance(raw, (list, tuple, set)):
        return ' | '.join(_normalize(x) for x in raw if x is not None)
    return _normalize(raw)


def assess_ingestion(case: dict) -> dict:
    """Return conservative routing; callers must not treat this as diagnosis.

    Reads: substance, symptoms, breathing_normal, amount, dog_weight_kg,
    minutes_since. The latter three are collected for veterinarian handoff,
    NOT used to calculate toxic doses.
    """
    if not isinstance(case, dict):
        raise TypeError('case must be a dictionary')
    symptoms = _symptom_text(case.get('symptoms'))
    substance = _normalize(case.get('substance'))
    breathing = case.get('breathing_normal')

    # Explicit breathing concern takes precedence even when substance is missing.
    if breathing is False:
        result = Assessment(EMERGENCY, 'Caller reported abnormal breathing',
                            'Seek emergency veterinary care immediately.',
                            'ABNORMAL_BREATHING')
    elif (flag := _matches(symptoms, RED_FLAG_PHRASES)):
        result = Assessment(EMERGENCY, f'Emergency symptom reported: {flag}',
                            'Seek emergency veterinary care immediately.',
                            'RED_FLAG_SYMPTOM')
    elif (concern := _matches(substance, CONCERN_PHRASES)):
        result = Assessment(CONTACT_VET_NOW,
                            f'Potentially hazardous ingestion reported: {concern}',
                            'Contact a veterinarian or animal poison-control service immediately.',
                            'KNOWN_CONCERN')
    elif substance:
        result = Assessment(CONTACT_VET_NOW,
                            'This demo cannot verify whether the reported ingestion is safe',
                            'Contact a veterinarian or animal poison-control service for advice.',
                            'UNVERIFIED_INGESTION')
    elif symptoms:
        result = Assessment(CONTACT_VET_NOW,
                            'Symptoms reported but substance is not identified',
                            'Contact a veterinarian promptly and identify the substance if possible.',
                            'SYMPTOMS_UNKNOWN_SUBSTANCE')
    else:
        result = Assessment(NEEDS_MORE_INFORMATION, 'Substance not yet identified',
                            'Ask what was eaten and whether the dog is breathing normally. '
                            'If ingestion is suspected, contact a veterinarian.',
                            'MISSING_SUBSTANCE')
    return asdict(result)
