"""Vocabulario, codificación, padding y DataLoader para nombres de dinosaurios."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import torch
from torch.utils.data import DataLoader, Dataset, random_split

PAD = "<PAD>"
SOS = "<SOS>"
EOS = "<EOS>"


class DinoVocab:
    """Vocabulario fijo: a-z + tokens especiales (29 símbolos)."""

    def __init__(self) -> None:
        chars = list("abcdefghijklmnopqrstuvwxyz")
        self.itos: list[str] = [PAD, SOS, EOS] + chars
        self.stoi: dict[str, int] = {c: i for i, c in enumerate(self.itos)}

    @property
    def pad_id(self) -> int:
        return self.stoi[PAD]

    @property
    def sos_id(self) -> int:
        return self.stoi[SOS]

    @property
    def eos_id(self) -> int:
        return self.stoi[EOS]

    def __len__(self) -> int:
        return len(self.itos)

    def encode(self, name: str) -> list[int]:
        return (
            [self.sos_id]
            + [self.stoi[c] for c in name.lower() if c in self.stoi]
            + [self.eos_id]
        )

    def decode(self, ids: Iterable[int]) -> str:
        out: list[str] = []
        for i in ids:
            tok = self.itos[i]
            if tok in (EOS, PAD):
                break
            if tok == SOS:
                continue
            out.append(tok)
        return "".join(out)


def load_names(csv_path: str | Path) -> list[str]:
    """Lee dinos.csv y normaliza: minúsculas, solo letras a-z."""
    import pandas as pd

    df = pd.read_csv(csv_path, header=None)
    names = df.iloc[:, 0].astype(str).str.lower().str.strip()
    names = names[names.str.match(r"^[a-z]+$")]
    return names.tolist()


class DinoDataset(Dataset):
    """Cada nombre se codifica con SOS/EOS y se rellena con PAD a max_len."""

    def __init__(self, names: list[str], vocab: DinoVocab, max_len: int) -> None:
        self.examples: list[torch.Tensor] = []
        for name in names:
            ids = vocab.encode(name)[:max_len]
            ids = ids + [vocab.pad_id] * (max_len - len(ids))
            self.examples.append(torch.tensor(ids, dtype=torch.long))

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        seq = self.examples[idx]
        return seq[:-1], seq[1:]


def make_dataloaders(
    csv_path: str | Path,
    batch_size: int = 64,
    val_split: float = 0.1,
    max_len: int | None = None,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader, DinoVocab, int]:
    vocab = DinoVocab()
    names = load_names(csv_path)
    if max_len is None:
        max_len = max(len(n) for n in names) + 2  # +SOS +EOS
    ds = DinoDataset(names, vocab, max_len)

    n_val = int(len(ds) * val_split)
    n_train = len(ds) - n_val
    g = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(ds, [n_train, n_val], generator=g)

    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=True),
        DataLoader(val_ds, batch_size=batch_size),
        vocab,
        max_len,
    )
