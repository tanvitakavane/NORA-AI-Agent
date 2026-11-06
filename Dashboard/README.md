# Nora AI — Member 3: Dashboard and Monitoring

## Files you own
- `dashboard/app.py`: FastAPI dashboard and WebSocket bridge to Member 2's `DEFAULT_BUS`.
- `dashboard/index.html`: live, responsive dashboard with case selection, assessment label, explanation, event timeline, and reconnect.
- `demo_dashboard.py`: simulated event demo, not a voice agent.
- `tests/test_dashboard.py`: API and WebSocket contract tests.
- `requirements-dev.txt`: local test dependencies.

## Critical integration contract
Member 2's `events.py` defines `DEFAULT_BUS`, `subscribe(callback)`, `recent(case_id=None)` and `publish(kind,payload,case_id)`. The dashboard subscribes to **the same Python object in the same process**. It consumes these existing event types: `case_updated`, `assessment`, `mock_alert`.

Member 4 must start the dashboard server **in the same process** as the LiveKit worker, or explicitly build a cross-process bridge. Running `uvicorn dashboard.app:app` in a separate terminal from the voice agent WILL NOT show its events. For the hackathon, a simple option is to start uvicorn in a daemon thread in the agent process:

```python
import threading
import uvicorn
from dashboard.app import app

def start_dashboard():
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='warning')

threading.Thread(target=start_dashboard, daemon=True).start()
```

Start it **once** in the process that owns the `CaseTools` instance, not per phone call. Confirm the official LiveKit worker architecture permits this; if the agent executes calls in a different process, use an explicit HTTP/Redis/IPC event bridge instead. Import `events.DEFAULT_BUS` consistently so Python does not load duplicate module copies.

## Test without LiveKit
1. Place `dashboard/` and `demo_dashboard.py` in the project root alongside Member 2's `events.py`.
2. `uv run --with fastapi --with uvicorn --with pytest --with httpx python -m pytest tests/test_dashboard.py -q`
3. `uv run --with fastapi --with uvicorn python demo_dashboard.py`
4. Open http://127.0.0.1:8000 and watch the synthetic event sequence.

## Production/ethics boundaries
- Only publish **sanitized** event metadata. Member 2 intentionally excludes phone numbers and raw case values from event payloads.
- Do not expose this demo dashboard on a public interface without authentication and access controls.
- This dashboard displays a **prototype routing assessment**, not a veterinary diagnosis or medical decision.
- Member 2 does not emit per-turn latency or passive-monitor emotion events. These are **not implemented**; add only if Member 4 provides measured latency events or a separately tested monitor.
- Browser history is in-memory only; refreshing reloads the bus's recent events. No persistence or real SMS.
