import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag import extract_text, get_rag_service


class FakeRAG:
    def ingest(self, name, raw):
        safe_name, text = extract_text(name, raw)
        return {'filename': safe_name, 'chunks': 1, 'sha256': 'test'}

    def answer(self, question):
        return {'answer': 'Kaynaklı örnek yanıt [1]', 'sources': [
            {'filename': 'test.txt', 'chunk_index': 0, 'score': 0.9, 'excerpt': 'örnek'}
        ]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('APP_API_KEY', 'test-secret')
    app.dependency_overrides[get_rag_service] = lambda: FakeRAG()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get('/api/health').json()['status'] == 'ok'


def test_auth_required(client):
    assert client.post('/api/ask', json={'question': 'Stok nedir?'}).status_code == 401


def test_ask(client):
    r = client.post('/api/ask', json={'question': 'Stok nedir?'},
                    headers={'X-API-Key': 'test-secret'})
    assert r.status_code == 200
    assert r.json()['sources'][0]['filename'] == 'test.txt'


def test_ingest(client):
    r = client.post('/api/ingest', files={'file': ('test.txt', 'Stok sayımı her cuma saat 17.00 yapılır.'.encode())},
                    headers={'X-API-Key': 'test-secret'})
    assert r.status_code == 200
    assert r.json()['filename'] == 'test.txt'


def test_oversize(client):
    r = client.post('/api/ingest', files={'file': ('big.txt', b'a' * (5 * 1024 * 1024 + 1))},
                    headers={'X-API-Key': 'test-secret'})
    assert r.status_code == 413


def test_sales_bad_month(client):
    r = client.get('/api/sales/summary?month=2026-99', headers={'X-API-Key': 'test-secret'})
    assert r.status_code == 422
