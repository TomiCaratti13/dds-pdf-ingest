"""Recibe PDF en memoria y coordina servicios con tiempos máximos explícitos."""
import asyncio
import hashlib
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile
from starlette.responses import JSONResponse
from app.core.config import settings
from app.services.upload_service import receive_pdf, PDF_UPLOAD_BODY

@asynccontextmanager
async def lifespan(app):
    app.state.client = httpx.AsyncClient(timeout=httpx.Timeout(settings.UPSTREAM_TIMEOUT, connect=3), trust_env=False)
    app.state.slots = asyncio.Queue(maxsize=settings.MAX_INFLIGHT)
    for _ in range(settings.MAX_INFLIGHT):
        app.state.slots.put_nowait(True)
    yield
    await app.state.client.aclose()

app = FastAPI(title="PDF Ingest", lifespan=lifespan)

async def admission():
    # Admisión antes de recibir el cuerpo: acota archivos simultáneos en RAM.
    try:
        app.state.slots.get_nowait()
    except asyncio.QueueEmpty:
        raise HTTPException(503, "Servicio ocupado", headers={"Retry-After": "1"})
    try:
        yield
    finally:
        app.state.slots.put_nowait(True)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingest"}

async def orchestrate(file: UploadFile, doc_id: str | None = None):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Se requiere extensión PDF")
    content = await file.read()
    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "Firma PDF inválida")
    try:
        extracted = await app.state.client.post(settings.EXTRACT_URL + "/extract", content=content, headers={"Content-Type": "application/pdf"})
        if extracted.status_code != 200:
            status = extracted.status_code if extracted.status_code in (400, 413, 429, 503) else 502
            return JSONResponse(status_code=status, content={"detail": "No se pudo extraer el PDF"}, headers={"Retry-After": "1"} if status in (429,503) else {})
        result = extracted.json()
        # /extract ofrece text además de Markdown: conserva el contrato de etapa 1.
        data = {"filename": file.filename, "text": result["text"], "checksum": hashlib.sha256(content).hexdigest(), "size": len(content)}
        url = settings.DOCUMENTS_URL + "/internal/documents"
        response = await (app.state.client.post(url, json=data) if doc_id is None else app.state.client.put(url + "/" + doc_id, json=data))
        if response.status_code not in (200,201,404,409,422,503):
            raise HTTPException(502, "Respuesta inesperada de documents")
        return JSONResponse(status_code=response.status_code, content=response.json(), headers={"Retry-After":"1"} if response.status_code == 503 else {})
    except httpx.TimeoutException:
        raise HTTPException(504, "Tiempo de espera del servicio agotado")
    except httpx.RequestError:
        raise HTTPException(502, "Servicio dependiente no disponible")
    except (ValueError, KeyError, TypeError):
        raise HTTPException(502, "Contrato de respuesta inválido")

@app.post("/documents/upload", dependencies=[Depends(admission)], openapi_extra=PDF_UPLOAD_BODY)
async def upload(file: UploadFile = Depends(receive_pdf)):
    return await orchestrate(file)

@app.put("/documents/{doc_id}", dependencies=[Depends(admission)], openapi_extra=PDF_UPLOAD_BODY)
async def replace(doc_id: str, file: UploadFile = Depends(receive_pdf)):
    return await orchestrate(file, doc_id)
