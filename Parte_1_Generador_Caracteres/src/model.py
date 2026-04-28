"""Modelo CharRNN parametrizado por tipo de celda (rnn / lstm / gru)."""
from __future__ import annotations

import torch
import torch.nn as nn

_CELLS: dict[str, type[nn.Module]] = {
    "rnn": nn.RNN,
    "lstm": nn.LSTM,
    "gru": nn.GRU,
}


class CharRNN(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 32,
        hidden_dim: int = 128,
        num_layers: int = 1,
        cell_type: str = "lstm",
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        cell_type = cell_type.lower()
        if cell_type not in _CELLS:
            raise ValueError(f"cell_type debe ser uno de {list(_CELLS)}")
        self.cell_type = cell_type
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.rnn = _CELLS[cell_type](
            embed_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Linear(hidden_dim, vocab_size)

    def forward(
        self, x: torch.Tensor, hidden: torch.Tensor | tuple | None = None
    ) -> tuple[torch.Tensor, torch.Tensor | tuple]:
        emb = self.embed(x)
        out, hidden = self.rnn(emb, hidden)
        return self.head(out), hidden
