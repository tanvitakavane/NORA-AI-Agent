"""FastAPI dashboard wired to Member 2's in-process EventBus.

IMPORTANT: Mount this app in the SAME Python process as the voice agent, or
use a separately designed transport bridge. An independent uvicorn process
cannot see events published by the agent's DEFAULT_BUS.
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from queue import Empty, Full, Queue
from threading import RLock

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

try:
    from events import DEFAULT_BUS
except ImportError as exc:
    raise RuntimeError('Copy dashboard/ beside Member 2 events.py') from exc

STATIC = Path(__file__).resolve().parent
MAX_QUEUED = 100

class DashboardBridge:
    def __init__(self, bus=DEFAULT_BUS):
        self.bus = bus
        self._lock = RLock()
        self._clients: set[Queue] = set()
        self.bus.subscribe(self._on_event)

    def _on_event(self, event):
        # Only publish event metadata already sanitized by Member 2.
        with self._lock:
            clients = tuple(self._clients)
        for q in clients:
            try:
                q.put_nowait(event)
            except Full:
                try:
                    q.get_nowait()  # Drop oldest rather than block a phone call.
                    q.put_nowait(event)
                except (Empty, Full):
                    pass

    def connect(self):
        q = Queue(maxsize=MAX_QUEUED)
        with self._lock:
            self._clients.add(q)
        return q

    def disconnect(self, q):
        with self._lock:
            self._clients.discard(q)

bridge = DashboardBridge()
app = FastAPI(title='Nora Demo Dashboard')

@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')

@app.get('/api/events')
def events(case_id: str | None = None):
    # Demo only: bind to localhost or protect access before public deployment.
    return {'events': bridge.bus.recent(case_id=case_id)[-100:]}

@app.get('/api/health')
def health():
    return {'status': 'ok', 'transport': 'same-process-event-bus'}

@app.websocket('/ws')
async def websocket_events(ws: WebSocket):
    await ws.accept()
    q = bridge.connect()
    try:
        # Send initial snapshot; then stream events from the shared process.
        await ws.send_json({'type': 'history', 'events': bridge.bus.recent()[-100:]})
        while True:
            try:
                event = await asyncio.to_thread(q.get, True, 1.0)
            except Empty:
                continue
            await ws.send_json({'type': 'event', 'event': event})
    except (WebSocketDisconnect, RuntimeError, OSError):
        pass
    finally:
        bridge.disconnect(q)
