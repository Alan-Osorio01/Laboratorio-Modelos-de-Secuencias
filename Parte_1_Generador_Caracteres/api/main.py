"""FastAPI que sirve el generador de nombres desde SageMaker.

Se expone vía ngrok (puerto 8000). El frontend lo llama directamente.

Variables de entorno:
    CHECKPOINT  — ruta a best_model.pt (default: /home/ec2-user/SageMaker/models/best_model.pt)
    DATA_CSV    — ruta a dinos.csv (default: /home/ec2-user/SageMaker/data/dinos.csv)
    DEVICE      — 'cuda' o 'cpu' (default: auto-detect)

Uso:
    uvicorn Parte_1_Generador_Caracteres.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..src.dataset import load_names
from ..src.sample import generate_unique, load_model

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
        _model, _vocab, _max_len = load_model(CHECKPOINT, device=DEVICE)
        _seen = set(load_names(DATA_CSV)) if Path(DATA_CSV).exists() else set()


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
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    _ensure_loaded()
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
        raise HTTPException(status_code=500, detail="No se pudo generar nombres únicos.")
    return GenerateResponse(names=names)
