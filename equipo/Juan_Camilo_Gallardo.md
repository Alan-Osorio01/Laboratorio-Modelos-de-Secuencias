# Juan Camilo Gallardo — Tareas asignadas

## Resumen

Te toca la **variante LSTM** del generador y **toda la Parte 2** (Ollama corriendo en SageMaker con persistencia y túnel ngrok).

## Partes en las que estás involucrado

- **Parte 1** (variante LSTM): tu notebook personal.
- **Parte 2** (descripciones con Ollama): owner de toda la sección.

---

## Parte 1 — Variante LSTM

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/notebooks/02_lstm_JuanCamiloGallardo.ipynb](../Parte_1_Generador_Caracteres/notebooks/02_lstm_JuanCamiloGallardo.ipynb) — tu notebook (créalo).
- [Parte_1_Generador_Caracteres/src/model.py](../Parte_1_Generador_Caracteres/src/model.py) — colaboras en la clase `CharRNN`.

### Checklist

- [ ] Esperar `01_preprocessing.ipynb` listo (compartido).
- [ ] Crear `02_lstm_JuanCamiloGallardo.ipynb`, usar `CharRNN(cell_type='lstm')`.
- [ ] Entrenar 30–50 épocas, registrar en MLflow con `run_name="LSTM_JuanCamiloGallardo"`.
- [ ] Reportar: loss curves, perplejidad, ejemplo de 5 nombres muestreados.
- [ ] Si tu modelo es el mejor, copiar el checkpoint a `Parte_1_Generador_Caracteres/models/best_model.pt`.

### Hiperparámetros sugeridos

- `embed_dim=32`, `hidden_dim=128`, `num_layers=1` (probar también `num_layers=2`).
- `lr=1e-3` (Adam), `batch_size=64`.
- LSTM suele converger más estable que RNN simple — aprovéchalo para probar `dropout=0.2`.

---

## Parte 2 — Ollama en SageMaker

Eres el dueño de toda la subcarpeta [Parte_2_Ollama_Descripciones/](../Parte_2_Ollama_Descripciones/).

### Archivos que vas a crear

- [Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh](../Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh) — lifecycle script `on-start` de SageMaker.
- [Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh](../Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh) — `docker run` + `ollama pull`.
- [Parte_2_Ollama_Descripciones/infra/ngrok_tunnel.sh](../Parte_2_Ollama_Descripciones/infra/ngrok_tunnel.sh) — túnel a `localhost:11434`.
- [Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb](../Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb) — el notebook que genera las 10 descripciones.

### Checklist

- [ ] Crear notebook SageMaker `m5.xlarge`.
- [ ] Pegar `ollama_lifecycle_onstart.sh` como **lifecycle config on-start** (no on-create) — debe:
  - Crear `/home/ec2-user/SageMaker/docker` si no existe.
  - Apuntar `Docker data-root` ahí (editar `/etc/docker/daemon.json` y reiniciar Docker).
- [ ] `ollama_docker_run.sh`:
  - `docker run -d --name ollama -v /home/ec2-user/SageMaker/ollama:/root/.ollama -p 11434:11434 ollama/ollama`
  - `docker exec ollama ollama pull gemma2:2b` (o `qwen2.5:3b`).
- [ ] `ngrok_tunnel.sh`: `ngrok http 11434` y copiar la URL pública.
- [ ] `04_ollama_descriptions.ipynb`:
  - Leer los 10 nombres de `../data/generated/names.csv`.
  - System prompt con contexto paleontológico (ver `README.md` de la Parte 2).
  - Por cada nombre, `requests.post(NGROK_URL+"/api/generate", json={...})`.
  - Guardar `{name, description}` en `../data/generated/descriptions.json`.

### Dependencias de otros

- Necesitas los **10 nombres** del muestreo (Parte 1, viene de `../data/generated/names.csv`).
- Tu URL de ngrok la consume **Alan** para configurar la Lambda → mándasela apenas la tengas.

### Riesgos y consejos

- **m5.xlarge es CPU-only**: NO uses modelos > 7B. `gemma2:2b` o `qwen2.5:3b` son la zona segura.
- **El túnel ngrok dura ~2 h en plan free**: si se cae, levantarlo de nuevo y avisar a Alan para que actualice la env var de la Lambda.
- **El lifecycle script puede fallar silenciosamente**: prueba primero apagando y prendiendo el notebook a ver si Ollama sobrevive.
