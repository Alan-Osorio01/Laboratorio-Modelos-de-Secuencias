# Parte 1 — Generador de caracteres (RNN/LSTM/GRU)

Modelo de lenguaje a nivel de caracteres que aprende los patrones de los nombres de dinosaurios reales y genera nuevas combinaciones.

## Entregables

1. Tres variantes entrenadas con celdas distintas (RNN, LSTM, GRU).
2. **10 mejores nombres generados** (originales, plausibles, variados).
3. **Nota breve (3–5 líneas)** con análisis comparativo de modelos y parámetros de muestreo (`temperature`, `top-k`, `top-p`) — en `../reports/sampling_comparison.md`.
4. Checkpoint del mejor modelo en `models/best_model.pt`.

## Estructura

```
Parte_1_Generador_Caracteres/
├── notebooks/
│   ├── 01_preprocessing.ipynb           # compartido — vocab, padding, X/Y split
│   ├── 02_rnn_AlanOsorio.ipynb          # variante RNN simple
│   ├── 02_lstm_JuanCamiloGallardo.ipynb # variante LSTM
│   ├── 02_gru_SantiagoDiaz.ipynb        # variante GRU
│   └── 03_sampling.ipynb                # compartido — temperatura + top-k + top-p
├── src/
│   ├── dataset.py    # vocab, codificación, padding, DataLoader
│   ├── model.py      # CharRNN(cell_type='rnn'|'lstm'|'gru')
│   ├── train.py      # bucle de entrenamiento + MLflow
│   └── sample.py     # generación con T, top-k, top-p
└── models/
    └── best_model.pt # se commitea (Git LFS si pesa más de 50 MB)
```

## Datos

- Fuente: <https://github.com/jpospinalo/MachineLearning/blob/main/nlp/dinos.csv>
- Localización: `../data/dinos.csv` (compartido entre todas las partes).

## Especificaciones

**Preprocesamiento**:
- Normalizar a minúsculas, filtrar no-alfabéticos.
- Vocabulario: `{a-z, <SOS>, <EOS>, <PAD>}` (29 tokens).
- `T = max(len(name)) + 2`; padding con `<PAD>`.
- `X = [x_0..x_{T-1}]`, `Y = [x_1..x_T]` con máscara para ignorar PAD en la pérdida.

**Modelo `CharRNN`**:
- `nn.Embedding(vocab_size, 32)` → celda recurrente (`hidden_dim=128`) → `nn.Linear` → logits.
- Pérdida: `CrossEntropyLoss(ignore_index=PAD_ID)`.
- Optimizador: Adam, `lr=1e-3`. Early stopping por val loss (~30–50 épocas).
- Tracking con MLflow (mismo patrón que sentiment140).

**Muestreo**:
- Generación autorregresiva desde `<SOS>` hasta `<EOS>` o `T`.
- Combinaciones a probar: `temperature ∈ {0.7, 1.0, 2.5, 4.0}`, `top_k ∈ {None, 5, 10}`, `top_p ∈ {None, 0.9, 0.95}`.
- Filtrar nombres ya presentes en `dinos.csv` (originalidad).
- CSV con todas las combinaciones en `../data/generated/names.csv`.

## Cómo correr

```bash
# entrenar (desde la raíz del repo)
python -m Parte_1_Generador_Caracteres.src.train --cell lstm --epochs 50

# samplear 10 nombres
python -m Parte_1_Generador_Caracteres.src.sample \
    --checkpoint Parte_1_Generador_Caracteres/models/best_model.pt \
    --n 10 --temperature 1.0 --top-p 0.9
```
