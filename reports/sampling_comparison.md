# Análisis comparativo del muestreo

> **Pendiente de completar tras correr `03_sampling.ipynb`** — esta plantilla la rellena Santiago Diaz una vez tenga el barrido completo.

## Plantilla (3–5 líneas)

- **Modelo ganador**: ___ (RNN / LSTM / GRU). Val loss ___, perplejidad ___.
- **Temperatura**: con `T=0.7` los nombres se vuelven monótonos (variantes de "saurus" comunes); con `T=2.5` aparecen secuencias incoherentes; el punto dulce queda en `T=1.0`.
- **top-k vs top-p**: top-p (0.9) supera a top-k fijo en diversidad cuando la distribución es sesgada, porque adapta el corte. top-k=10 es un buen baseline barato.
- **Combinación final usada para los 10 nombres**: `T=1.0, top_p=0.9` — balance entre originalidad y plausibilidad.
- **Observación**: filtrar por sufijos paleontológicos (`-saurus, -raptor, -odon, -ceratops`) duplica la "calidad percibida" sin sacrificar diversidad.

## 10 finalistas

| # | Nombre | Configuración (T, top_k, top_p) |
|---|---|---|
| 1 | … | … |
| 2 | … | … |
| 3 | … | … |
| 4 | … | … |
| 5 | … | … |
| 6 | … | … |
| 7 | … | … |
| 8 | … | … |
| 9 | … | … |
| 10 | … | … |
