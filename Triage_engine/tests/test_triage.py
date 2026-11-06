import pytest
from triage import assess_ingestion

@pytest.mark.parametrize('symptom', [
    'seizure', 'collapsed', 'trouble breathing', 'passed out', 'severe bleeding'
])
def test_emergency_symptoms_override_substance(symptom):
    out = assess_ingestion({'substance': 'bread', 'symptoms': [symptom]})
    assert out['label'] == 'EMERGENCY'
    assert out['rule_id'] == 'RED_FLAG_SYMPTOM'


def test_breathing_flag_overrides_all():
    out = assess_ingestion({'breathing_normal': False, 'substance': None})
    assert out['rule_id'] == 'ABNORMAL_BREATHING'

@pytest.mark.parametrize('substance', [
    'raisins', 'grapes', 'xylitol gum', 'antifreeze', 'rat poison',
    'ibuprofen tablets', 'dark chocolate', 'human medication'
])
def test_known_concern_routes_to_vet(substance):
    out = assess_ingestion({'substance': substance, 'symptoms': []})
    assert out['label'] == 'CONTACT_VET_NOW'
    assert out['rule_id'] == 'KNOWN_CONCERN'

@pytest.mark.parametrize('substance', ['unknown powder', 'bread', 'grass', 'grapefruit'])
def test_unverified_substances_not_declared_safe(substance):
    out = assess_ingestion({'substance': substance})
    assert out['label'] == 'CONTACT_VET_NOW'
    assert out['rule_id'] == 'UNVERIFIED_INGESTION'


def test_missing_substance_and_symptoms():
    assert assess_ingestion({})['label'] == 'NEEDS_MORE_INFORMATION'


def test_symptoms_without_substance():
    assert assess_ingestion({'symptoms': ['vomiting']})['label'] == 'CONTACT_VET_NOW'


def test_normal_breathing_does_not_override_emergency_symptom():
    assert assess_ingestion({'breathing_normal': True, 'symptoms': ['seizure']})['label'] == 'EMERGENCY'


def test_extra_fields_do_not_change_routing():
    a = assess_ingestion({'substance': 'chocolate'})
    b = assess_ingestion({'substance': 'chocolate', 'amount': 'a few',
                          'dog_weight_kg': 12, 'minutes_since': 30})
    assert a == b


def test_corrections_are_reassessed_not_cached():
    first = assess_ingestion({'substance': 'bread'})
    second = assess_ingestion({'substance': 'raisins'})
    assert first['rule_id'] == 'UNVERIFIED_INGESTION'
    assert second['rule_id'] == 'KNOWN_CONCERN'


def test_return_contract():
    assert set(assess_ingestion({})) == {'label', 'reason', 'next_step', 'rule_id'}


def test_rejects_wrong_case_type():
    with pytest.raises(TypeError):
        assess_ingestion(None)


def test_never_returns_monitor_home():
    for substance in [None, 'bread', 'grass', 'chocolate', 'raisins']:
        assert assess_ingestion({'substance': substance})['label'] != 'MONITOR_AT_HOME'
