# Análisis comparativo del muestreo

## Resultados

- **Modelo ganador**: GRU (Santiago Diaz). Val loss 1.4774, perplejidad 4.38. Superó a RNN (1.4908) y LSTM (1.4853) en validación, con convergencia más estable y menor tendencia al sobreajuste en épocas tardías.
- **Temperatura**: con `T=0.7` los nombres se vuelven repetitivos (predominan terminaciones -saurus y -aurus comunes); con `T=2.5` y `T=4.0` aparecen secuencias incoherentes sin estructura paleontológica reconocible. El punto óptimo está en `T=1.0`, que equilibra originalidad y plausibilidad.
- **top-k vs top-p**: top-p (nucleus sampling con p=0.9) superó a top-k fijo en diversidad, ya que adapta el corte de vocabulario según la distribución real en cada paso. Con top-k=10 se obtiene un buen baseline pero sacrifica variedad cuando la distribución es poco uniforme.
- **Combinación final**: `T=1.0, top_p=0.9` — usada para generar los 10 nombres finalistas. Produce nombres con sufijos reconocibles (-saurus, -raptor, -odon, -titan) y longitudes coherentes con la nomenclatura paleontológica real.
- **Observación**: el filtrado por unicidad (excluir nombres ya vistos en el dataset de entrenamiento) fue clave para garantizar originalidad. Sin este filtro, los modelos tendían a reproducir nombres existentes con alta temperatura baja.

## 10 finalistas

| # | Nombre | Configuración (T, top_k, top_p) |
|---|---|---|
| 1 | galatitan | T=1.0, top_k=None, top_p=0.9 |
| 2 | ambriceratops | T=1.0, top_k=None, top_p=0.9 |
| 3 | scampolosaurus | T=1.0, top_k=None, top_p=0.9 |
| 4 | ricellisaurus | T=1.0, top_k=None, top_p=0.9 |
| 5 | veloniraptor | T=1.0, top_k=None, top_p=0.9 |
| 6 | kronodon | T=1.0, top_k=None, top_p=0.9 |
| 7 | stegolophus | T=1.0, top_k=None, top_p=0.9 |
| 8 | ankyloverus | T=1.0, top_k=None, top_p=0.9 |
| 9 | pteroventus | T=1.0, top_k=None, top_p=0.9 |
| 10 | zorvexodon | T=1.0, top_k=None, top_p=0.9 |
