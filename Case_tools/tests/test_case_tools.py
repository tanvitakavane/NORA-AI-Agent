import pytest
from case_state import CaseState
from events import EventBus
from tools import CaseTools

@pytest.fixture
def tools():
    return CaseTools(bus=EventBus())

def test_default_state(tools):
    assert tools.get_case()['substance'] is None
    assert tools.get_case()['assessment'] is None

def test_update_substance(tools):
    assert tools.update_case('substance', ' raisins ')['substance'] == 'raisins'

def test_emergency_breathing(tools):
    tools.update_case('breathing_normal', False)
    assert tools.assess_case()['label'] == 'EMERGENCY'

def test_known_concern(tools):
    tools.update_case('substance', 'raisins')
    assert tools.assess_case()['label'] == 'CONTACT_VET_NOW'

def test_correction_invalidates_assessment(tools):
    tools.update_case('substance', 'chocolate')
    tools.assess_case()
    tools.update_case('substance', 'raisins')
    assert tools.get_case()['assessment'] is None
    assert tools.assess_case()['reason'].endswith('grapes_or_raisins')

def test_noop_does_not_invalidate(tools):
    tools.update_case('substance', 'raisins')
    tools.assess_case()
    tools.update_case('substance', 'raisins')
    assert tools.get_case()['assessment'] is not None

def test_unsupported_field(tools):
    with pytest.raises(ValueError): tools.update_case('label', 'MONITOR')

@pytest.mark.parametrize('value',[-1,0,201,'abc',True,float('nan')])
def test_invalid_weight(tools,value):
    with pytest.raises(ValueError): tools.update_case('dog_weight_kg',value)

@pytest.mark.parametrize('value',[-1,1.5,True,'not-a-number'])
def test_invalid_time(tools,value):
    with pytest.raises(ValueError): tools.update_case('minutes_since',value)

def test_symptom_list_and_correction(tools):
    tools.update_case('symptoms',['seizure','seizure'])
    assert tools.get_case()['symptoms'] == ['seizure']
    assert tools.assess_case()['label'] == 'EMERGENCY'
    tools.update_case('symptoms',[])
    assert tools.get_case()['assessment'] is None

def test_mock_alert_not_sent(tools):
    alert = tools.alert_on_call_vet('Please call this case back')
    assert alert['status'] == 'MOCK_ALERT_CREATED'
    assert alert['delivered'] is False

def test_invalid_summary(tools):
    with pytest.raises(ValueError): tools.alert_on_call_vet('  ')

def test_separate_calls_isolated():
    a,b=CaseTools(bus=EventBus()),CaseTools(bus=EventBus())
    a.update_case('substance','raisins')
    assert b.get_case()['substance'] is None

def test_events_no_callback_leak(tools):
    tools.update_case('callback','929-555-0101')
    assert '9295550101' not in str(tools.bus.recent())

def test_event_subscriber_exception_isolated(tools):
    tools.bus.subscribe(lambda event: 1/0)
    tools.update_case('substance','chocolate')
    assert len(tools.bus.recent()) == 1

def test_snapshot_defensive_copy(tools):
    tools.update_case('symptoms',['collapse'])
    s=tools.get_case()
    s['symptoms'].append('fake')
    assert tools.get_case()['symptoms'] == ['collapse']

def test_history_tracks_correction(tools):
    tools.update_case('substance','chocolate')
    tools.update_case('substance','raisins')
    assert tools.get_case()['history'][-1]['previous'] == 'chocolate'

def test_boolean_type_strict(tools):
    with pytest.raises(ValueError): tools.update_case('breathing_normal','false')

def test_alert_after_correction_reassesses(tools):
    tools.update_case('substance','chocolate')
    tools.assess_case()
    tools.update_case('breathing_normal',False)
    assert tools.alert_on_call_vet('Breathing issue')['triage_label']=='EMERGENCY'
