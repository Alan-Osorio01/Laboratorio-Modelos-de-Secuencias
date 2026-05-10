"""FastAPI que sirve el generador de nombres desde SageMaker.

Se expone vía ngrok (puerto 8000). El frontend lo llama directamente.

Variables de entorno:
    CHECKPOINT  — ruta a best_model.pt (default: /home/ec2-user/SageMaker/models/best_model.pt)
    DATA_CSV    — ruta a dinos.csv (default: /home/ec2-user/SageMaker/data/dinos.csv)
    DEVICE      — 'cuda' o 'cpu' (default: auto-detect)
    LOG_FILE    — ruta al log estructurado (default: /var/log/dino-api.log)

Uso:
    uvicorn Parte_1_Generador_Caracteres.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import time
import random
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
import torch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..src.dataset import load_names
from ..src.sample import generate_unique, load_model

# ---------------------------------------------------------------------------
# Logging estructurado — escribe a LOG_FILE y también a stderr
# ---------------------------------------------------------------------------
LOG_FILE = os.environ.get("LOG_FILE", "/var/log/dino-api.log")

_handlers: list[logging.Handler] = [logging.StreamHandler()]
try:
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    _handlers.append(
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
    )
except PermissionError:
    pass  # en entornos sin /var/log solo escribe a stderr

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=_handlers,
    force=True,
)
logger = logging.getLogger("dino-api")

CHECKPOINT = os.environ.get(
    "CHECKPOINT",
    "/home/ec2-user/SageMaker/models/best_model.pt",
)
DATA_CSV = os.environ.get(
    "DATA_CSV",
    "/home/ec2-user/SageMaker/data/dinos.csv",
)
DEVICE = os.environ.get(
    "DEVICE",
    "cuda" if torch.cuda.is_available() else "cpu",
)
# Ollama corre en el mismo host (localhost:11434). El frontend llama a /api/generate
# en esta misma API y nosotros hacemos el proxy internamente.
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")

app = FastAPI(
    title="Dino Generator API",
    description="Generador de nombres de dinosaurios con CharRNN. Servido desde SageMaker.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _log_requests(request: Request, call_next) -> Response:
    t0 = time.monotonic()
    response = await call_next(request)
    ms = round((time.monotonic() - t0) * 1000)
    logger.info(
        '"method":"%s","path":"%s","status":%d,"ms":%d',
        request.method,
        request.url.path,
        response.status_code,
        ms,
    )
    return response


# Carga del modelo en memoria global (un solo cold start por proceso uvicorn)
_model = None
_vocab = None
_max_len = None
_seen: set[str] = set()


def _ensure_loaded() -> None:
    global _model, _vocab, _max_len, _seen
    if _model is None:
        if not Path(CHECKPOINT).exists():
            raise FileNotFoundError(f"Checkpoint no encontrado: {CHECKPOINT}")
        logger.info('"event":"model_load","checkpoint":"%s","device":"%s"', CHECKPOINT, DEVICE)
        _model, _vocab, _max_len = load_model(CHECKPOINT, device=DEVICE)
        _seen = set(load_names(DATA_CSV)) if Path(DATA_CSV).exists() else set()
        logger.info('"event":"model_ready","cell_type":"%s","vocab_size":%d', _model.cell_type, len(_vocab))


class GenerateRequest(BaseModel):
    n: int = Field(default=1, ge=1, le=20)
    temperature: float = Field(default=1.0, gt=0.0)
    top_k: int | None = Field(default=None, ge=1)
    top_p: float | None = Field(default=0.9, gt=0.0, le=1.0)


class GenerateResponse(BaseModel):
    names: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    try:
        _ensure_loaded()
        return {"status": "ok", "cell_type": _model.cell_type, "device": str(DEVICE)}
    except Exception as exc:
        logger.error('"event":"health_error","detail":"%s"', exc)
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    _ensure_loaded()
    logger.info(
        '"event":"generate_request","n":%d,"temperature":%s,"top_k":%s,"top_p":%s',
        req.n, req.temperature, req.top_k, req.top_p,
    )
    names = generate_unique(
        _model, _vocab, _max_len,
        n=req.n,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        seen=_seen,
        device=DEVICE,
    )
    if not names:
        logger.warning('"event":"generate_empty","n":%d', req.n)
        raise HTTPException(status_code=500, detail="No se pudo generar nombres únicos.")
    logger.info('"event":"generate_ok","names":%s', names)
    return GenerateResponse(names=names)


@app.post("/api/generate")
async def ollama_proxy(request: Request) -> JSONResponse:
    """Proxy transparente hacia Ollama en localhost:11434.

    El plan free de ngrok da una sola URL — el frontend apunta todo
    a esta API y este endpoint reenvía las peticiones de descripción a Ollama.
    """
    body: Any = await request.json()
    logger.info('"event":"ollama_proxy","model":"%s"', body.get("model", "?"))
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{OLLAMA_BASE}/api/generate", json=body)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        logger.error('"event":"ollama_unreachable","base":"%s"', OLLAMA_BASE)
        raise HTTPException(status_code=503, detail="Ollama no disponible en el host.")


class ImageRequest(BaseModel):
    name: str
    description: str = ""


@app.post("/image")
def generate_image(req: ImageRequest) -> JSONResponse:
    """Genera URL de imagen usando Pollinations.ai (sin GPU, sin cuenta extra).

    El frontend apunta DIFFUSION_URL a esta misma API — un solo ngrok para todo.
    """
    prompt = (
        f"A paleo-illustration of a dinosaur named {req.name}. "
        f"{req.description} "
        "Realistic museum diorama style, full body visible, neutral background, "
        "high detail, no text, no watermark."
    )
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
    logger.info('"event":"image_request","name":"%s"', req.name)
    return JSONResponse({"image_url": image_url})
