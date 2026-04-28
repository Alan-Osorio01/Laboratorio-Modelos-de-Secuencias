"""Generación autorregresiva de nombres con temperatura, top-k y top-p.

Uso:
    python -m Parte_1_Generador_Caracteres.src.sample \
        --checkpoint Parte_1_Generador_Caracteres/models/best_model.pt \
        --n 10 --temperature 1.0 --top-p 0.9
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn.functional as F

from .dataset import DinoVocab, load_names
from .model import CharRNN


def top_k_filter(logits: torch.Tensor, top_k: int | None) -> torch.Tensor:
    if top_k is None or top_k <= 0:
        return logits
    top_vals, _ = torch.topk(logits, top_k)
    cutoff = top_vals[..., -1, None]
    return torch.where(logits < cutoff, torch.full_like(logits, float("-inf")), logits)


def top_p_filter(logits: torch.Tensor, top_p: float | None) -> torch.Tensor:
    if top_p is None or top_p >= 1.0:
        return logits
    sorted_logits, sorted_idx = torch.sort(logits, descending=True)
    probs = F.softmax(sorted_logits, dim=-1)
    cum = torch.cumsum(probs, dim=-1)
    mask = cum > top_p
    mask[..., 0] = False  # mantener siempre el top-1
    sorted_logits = sorted_logits.masked_fill(mask, float("-inf"))
    return sorted_logits.gather(-1, sorted_idx.argsort(-1))


def sample_one(
    model: CharRNN,
    vocab: DinoVocab,
    max_len: int,
    temperature: float = 1.0,
    top_k: int | None = None,
    top_p: float | None = None,
    device: str | torch.device = "cpu",
) -> str:
    model.eval()
    forbidden = {vocab.pad_id, vocab.sos_id}
    x = torch.tensor([[vocab.sos_id]], device=device)
    hidden = None
    out_ids: list[int] = []
    with torch.no_grad():
        for _ in range(max_len):
            logits, hidden = model(x, hidden)
            logits = logits[:, -1, :] / max(temperature, 1e-6)
            for tid in forbidden:
                logits[0, tid] = float("-inf")
            logits = top_k_filter(logits, top_k)
            logits = top_p_filter(logits, top_p)
            probs = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(probs, 1)
            tok = nxt.item()
            if tok == vocab.eos_id:
                break
            out_ids.append(tok)
            x = nxt
    return vocab.decode(out_ids)


def load_model(
    checkpoint_path: str | Path, device: str | torch.device = "cpu"
) -> tuple[CharRNN, DinoVocab, int]:
    ck = torch.load(checkpoint_path, map_location=device, weights_only=False)
    args = ck["args"]
    vocab = DinoVocab()
    vocab.itos = ck["vocab_itos"]
    vocab.stoi = {c: i for i, c in enumerate(vocab.itos)}
    model = CharRNN(
        len(vocab),
        embed_dim=args["embed"],
        hidden_dim=args["hidden"],
        cell_type=args["cell"],
        num_layers=args["layers"],
    ).to(device)
    model.load_state_dict(ck["model"])
    return model, vocab, ck["max_len"]


def generate_unique(
    model: CharRNN,
    vocab: DinoVocab,
    max_len: int,
    n: int,
    temperature: float,
    top_k: int | None,
    top_p: float | None,
    seen: set[str],
    device: str | torch.device,
    max_attempts_factor: int = 50,
    min_length: int = 4,
) -> list[str]:
    """Muestrea hasta obtener `n` nombres originales (no en `seen`)."""
    out: list[str] = []
    out_set: set[str] = set()
    attempts = 0
    while len(out) < n and attempts < n * max_attempts_factor:
        name = sample_one(model, vocab, max_len, temperature, top_k, top_p, device)
        attempts += 1
        if (
            len(name) >= min_length
            and name not in seen
            and name not in out_set
        ):
            out.append(name)
            out_set.add(name)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--top-p", type=float, default=None)
    p.add_argument(
        "--seen",
        default="data/dinos.csv",
        help="CSV con nombres reales — se excluyen para garantizar originalidad.",
    )
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, vocab, max_len = load_model(args.checkpoint, device)
    seen = set(load_names(args.seen)) if args.seen else set()
    names = generate_unique(
        model, vocab, max_len, args.n,
        args.temperature, args.top_k, args.top_p, seen, device,
    )
    for name in names:
        print(name)


if __name__ == "__main__":
    main()
