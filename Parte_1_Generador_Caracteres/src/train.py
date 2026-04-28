"""Bucle de entrenamiento del CharRNN.

Uso:
    python -m Parte_1_Generador_Caracteres.src.train --cell gru --epochs 50
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .dataset import DinoVocab, make_dataloaders
from .model import CharRNN


def evaluate(
    model: CharRNN, loader: DataLoader, criterion: nn.Module, device: torch.device
) -> float:
    model.eval()
    total, count = 0.0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits, _ = model(x)
            loss = criterion(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            total += loss.item() * x.size(0)
            count += x.size(0)
    return total / max(count, 1)


def train(args: argparse.Namespace) -> tuple[dict[str, list[float]], float]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[train] device={device}, cell={args.cell}")

    train_loader, val_loader, vocab, max_len = make_dataloaders(
        args.data, batch_size=args.batch_size
    )
    model = CharRNN(
        len(vocab),
        embed_dim=args.embed,
        hidden_dim=args.hidden,
        num_layers=args.layers,
        cell_type=args.cell,
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss(ignore_index=vocab.pad_id)

    history: dict[str, list[float]] = {"train_loss": [], "val_loss": []}
    best_val = float("inf")
    patience = 0

    use_mlflow = False
    try:
        import mlflow

        mlflow.set_experiment("dino-charrnn")
        mlflow.start_run(run_name=f"{args.cell}_{args.run_tag}")
        mlflow.log_params(vars(args))
        use_mlflow = True
    except ImportError:
        print("[train] mlflow no disponible, sigo sin tracking.")

    Path(args.checkpoint).parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        ep_loss, ep_n = 0.0, 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits, _ = model(x)
            loss = criterion(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            loss.backward()
            opt.step()
            ep_loss += loss.item() * x.size(0)
            ep_n += x.size(0)

        train_loss = ep_loss / ep_n
        val_loss = evaluate(model, val_loader, criterion, device)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        print(f"epoch {epoch + 1:02d} | train {train_loss:.4f} | val {val_loss:.4f}")

        if use_mlflow:
            import mlflow

            mlflow.log_metrics(
                {"train_loss": train_loss, "val_loss": val_loss}, step=epoch
            )

        if val_loss < best_val:
            best_val = val_loss
            patience = 0
            torch.save(
                {
                    "model": model.state_dict(),
                    "args": vars(args),
                    "vocab_itos": vocab.itos,
                    "max_len": max_len,
                },
                args.checkpoint,
            )
        else:
            patience += 1
            if patience >= args.patience:
                print(f"[train] early stop @ epoch {epoch + 1}")
                break

    if use_mlflow:
        import mlflow

        mlflow.log_artifact(args.checkpoint)
        mlflow.end_run()

    return history, best_val


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/dinos.csv")
    p.add_argument("--cell", choices=["rnn", "lstm", "gru"], default="lstm")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--embed", type=int, default=32)
    p.add_argument("--hidden", type=int, default=128)
    p.add_argument("--layers", type=int, default=1)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--patience", type=int, default=5)
    p.add_argument(
        "--checkpoint",
        default="Parte_1_Generador_Caracteres/models/best_model.pt",
    )
    p.add_argument("--run-tag", default="default")
    return p


if __name__ == "__main__":
    train(build_parser().parse_args())
