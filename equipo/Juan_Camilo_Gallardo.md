# Juan Camilo Gallardo — Tareas asignadas

## Resumen

Te toca la **variante LSTM** del generador, y el **núcleo del backend en SageMaker**: tu instancia aloja **Ollama + el FastAPI del generador**, ambos detrás de **dos túneles ngrok**.

> **Cambio de arquitectura**: la misma SageMaker que sirve Ollama también sirve el modelo del generador (FastAPI). Volumen EBS **mínimo 100 GB**.

## Partes en las que estás involucrado

- **Parte 1** (variante LSTM).
- **Parte 2** (SageMaker: Ollama + Generator API + ngrok) — owner total.

---

## Parte 1 — Variante LSTM

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/notebooks/02_lstm_JuanCamiloGallardo.ipynb](../Parte_1_Generador_Caracteres/notebooks/02_lstm_JuanCamiloGallardo.ipynb) — tu notebook (créalo).

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

## Parte 2 — SageMaker (Ollama + Generator + ngrok)

Eres el dueño de toda la subcarpeta [Parte_2_Ollama_Descripciones/](../Parte_2_Ollama_Descripciones/) y de la instancia SageMaker.

### Especificaciones de la instancia

| Item | Valor |
|---|---|
| Tipo | `m5.xlarge` (CPU, 4 vCPU, 16 GB RAM) |
| **Volumen EBS** | **mínimo 100 GB** (no negociable — Docker + modelos no caben con menos) |
| Lifecycle | `on-start` (no `on-create`) |

### Archivos que vas a tocar

- [Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh](../Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh) — lifecycle script `on-start`.
- [Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh](../Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh) — `docker run` + `ollama pull`.
- [Parte_2_Ollama_Descripciones/infra/start_generator_api.sh](../Parte_2_Ollama_Descripciones/infra/start_generator_api.sh) — uvicorn del FastAPI (ya está el esqueleto).
- [Parte_2_Ollama_Descripciones/infra/ngrok_tunnels.sh](../Parte_2_Ollama_Descripciones/infra/ngrok_tunnels.sh) — DOS túneles simultáneos (ya está).
- [Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb](../Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb) — genera las 10 descripciones.

### Checklist

- [ ] Crear notebook SageMaker `m5.xlarge` con **volumen 100 GB**.
- [ ] Pegar `ollama_lifecycle_onstart.sh` como **lifecycle config on-start**. Debe:
  - Crear `/home/ec2-user/SageMaker/{docker,ollama,models,logs}`.
  - Apuntar `Docker data-root` a `/home/ec2-user/SageMaker/docker` (editar `/etc/docker/daemon.json` y reiniciar Docker).
- [ ] Subir `best_model.pt` (de la Parte 1) a `/home/ec2-user/SageMaker/models/`.
- [ ] Subir/clonar el repo en `/home/ec2-user/SageMaker/Laboratorio-Modelos-de-Secuencias/`.
- [ ] Correr en orden:
  ```bash
  bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh
  bash Parte_2_Ollama_Descripciones/infra/start_generator_api.sh
  NGROK_AUTHTOKEN=... bash Parte_2_Ollama_Descripciones/infra/ngrok_tunnels.sh
  ```
- [ ] Copiar las 2 URLs públicas y mandarlas a **Alan** (las pega en `web/config.js`).
- [ ] Validar:
  - `curl https://<generator-url>.ngrok-free.app/health` → `{"status":"ok"}`
  - `curl -X POST https://<ollama-url>.ngrok-free.app/api/generate -d '{"model":"gemma2:2b","prompt":"hola","stream":false}'` → respuesta del LLM.
- [ ] Ejecutar `04_ollama_descriptions.ipynb`:
  - Leer los 10 nombres de `../data/generated/top10_names.json` (de Santiago).
  - System prompt con contexto paleontológico.
  - Generar y guardar en `../data/generated/descriptions.json`.

### Modelos recomendados para Ollama

- `gemma2:2b` o `qwen2.5:3b` (CPU, 16 GB RAM, ambos caben en 100 GB).
- **Evitar** modelos > 7B en `m5.xlarge`.

### Dependencias de otros

- Necesitas los **10 nombres** de la Parte 1 (Santiago, viene de `../data/generated/top10_names.json`).
- Necesitas el **`best_model.pt`** de la Parte 1 (quien gane entre RNN/LSTM/GRU).
- Tus URLs de ngrok las consumen **Alan** (las inyecta en el frontend) y **Santiago** (las usa en su notebook de difusión para enriquecer prompts).

### Riesgos y consejos

- **Las URLs de ngrok rotan ~2 h en plan free**: cuando rote, mandar la nueva a Alan para redesplegar el frontend. Considerar plan paid o `ngrok reserved domain` si lo permite el presupuesto.
- **El lifecycle script puede fallar silenciosamente**: prueba primero apagando y prendiendo el notebook a ver si Ollama y el generator API sobreviven.
- **`best_model.pt` debe vivir en `/SageMaker/models/`** (persistente). Si lo dejas en `/tmp` o el home, se borra al apagar.
