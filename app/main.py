"""Enterprise Local RAG demonstration API; not a production security boundary."""
from __future__ import annotations
import hmac
import os
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.rag import MAX_FILE_BYTES, get_rag_service
from app.sales import monthly_summary

app = FastAPI(title='Enterprise Local RAG Demo', version='0.1.0')
STATIC_INDEX = Path(__file__).resolve().parent.parent / 'static' / 'index.html'


def require_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv('APP_API_KEY', '')
    if not expected:
        raise HTTPException(503, 'Sunucuda APP_API_KEY tanımlanmamış.')
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(401, 'Geçersiz API anahtarı.')


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=800)


@app.get('/', include_in_schema=False)
def homepage():
    return FileResponse(STATIC_INDEX)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'enterprise-local-rag', 'version': '0.1.0'}


@app.post('/api/ingest', dependencies=[Depends(require_api_key)])
async def ingest(file: UploadFile = File(...), service=Depends(get_rag_service)):
    raw = await file.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(413, 'Dosya 5 MB sınırını aşıyor.')
    try:
        return service.ingest(file.filename or '', raw)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, 'Belge işleme servisine şu anda erişilemiyor.') from exc


@app.post('/api/ask', dependencies=[Depends(require_api_key)])
def ask(payload: AskRequest, service=Depends(get_rag_service)):
    try:
        return service.answer(payload.question)
    except Exception as exc:
        raise HTTPException(503, 'Yerel model veya vektör veritabanı kullanılamıyor.') from exc


@app.get('/api/sales/summary', dependencies=[Depends(require_api_key)])
def sales_summary(month: str = '2026-11'):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month):
        raise HTTPException(422, 'Ay YYYY-MM formatında olmalıdır.')
    try:
        return monthly_summary(month)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
