from fastapi.testclient import TestClient
from dashboard.app import app, bridge

def test_health():
    with TestClient(app) as client:
        assert client.get('/api/health').json()['status'] == 'ok'
        assert client.get('/').status_code == 200

def test_member2_bus_contract():
    with TestClient(app) as client:
        bridge.bus.publish('case_updated', {'field':'substance','revision':1,'assessment_stale':True}, 'TEST-M3')
        r=client.get('/api/events', params={'case_id':'TEST-M3'})
        assert r.status_code == 200
        assert r.json()['events'][-1]['type'] == 'case_updated'

def test_websocket_stream():
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as ws:
            assert ws.receive_json()['type'] == 'history'
            bridge.bus.publish('assessment', {'label':'CONTACT_VET_NOW','reason':'test','next_step':'call vet','rule_id':'TEST'}, 'TEST-WS')
            msg=ws.receive_json()
            assert msg['type'] == 'event'
            assert msg['event']['case_id'] == 'TEST-WS'
