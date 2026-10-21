import httpx
from fastapi.testclient import TestClient
from app.main import app

def test_orchestration_plain_text_and_checksum():
    calls = []
    def handler(request):
        calls.append(request)
        if request.url.path == "/extract":
            return httpx.Response(200, json={"content":"## Página 1", "text":"Texto", "page_count":1})
        return httpx.Response(201, json={"id":"123", "text":"Texto"})
    with TestClient(app) as client:
        previous = app.state.client
        app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        assert client.post("/documents/upload", files={"file":("a.pdf", b"%PDF-example")}).status_code == 201
        assert b'"text":"Texto"' in calls[1].content
        app.state.client = previous

def test_invalid_and_busy_are_rejected_before_extraction():
    with TestClient(app) as client:
        assert client.post("/documents/upload", files={"file":("a.pdf", b"bad")}).status_code == 400
        tokens = [app.state.slots.get_nowait() for _ in range(app.state.slots.qsize())]
        assert client.post("/documents/upload", files={"file":("a.pdf", b"%PDF-test")}).status_code == 503
        for token in tokens:
            app.state.slots.put_nowait(token)
