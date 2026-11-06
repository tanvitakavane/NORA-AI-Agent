"""Run with `python demo_dashboard.py` after placing beside Member 2's files.
Demo events are synthetic; this does not connect to the phone agent.
"""
import time
import threading
import uvicorn
from events import DEFAULT_BUS
from dashboard.app import app

def simulate():
    time.sleep(1)
    cid = 'DEMO-CASE-01'
    DEFAULT_BUS.publish('case_updated', {'field': 'substance', 'revision': 1, 'assessment_stale': True}, cid)
    time.sleep(2)
    DEFAULT_BUS.publish('assessment', {'revision': 1, 'label': 'CONTACT_VET_NOW', 'reason': 'Potentially hazardous substance reported', 'next_step': 'Contact a veterinarian or animal poison-control service.', 'rule_id': 'KNOWN_CONCERN'}, cid)
    time.sleep(2)
    DEFAULT_BUS.publish('mock_alert', {'status': 'MOCK_ALERT_CREATED', 'alert_id': 'MOCK-001', 'triage_label': 'CONTACT_VET_NOW'}, cid)

if __name__ == '__main__':
    threading.Thread(target=simulate, daemon=True).start()
    uvicorn.run(app, host='127.0.0.1', port=8000)
