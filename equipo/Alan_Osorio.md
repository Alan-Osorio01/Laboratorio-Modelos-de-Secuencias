# Alan Osorio — Tareas asignadas

## Resumen

Te toca la **variante RNN simple** del generador y **toda la infraestructura AWS** que sostiene la Parte 4. Eres el responsable de que el sitio web funcione end-to-end.

## Partes en las que estás involucrado

- **Parte 1** (variante RNN): tu notebook personal.
- **Parte 4** (integración web): owner del backend Lambda y del despliegue.

---

## Parte 1 — Variante RNN simple

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb](../Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb) — tu notebook (créalo).
- [Parte_1_Generador_Caracteres/src/model.py](../Parte_1_Generador_Caracteres/src/model.py) — colaboras con Juan Camilo y Santiago en la clase `CharRNN(cell_type=...)`.

### Checklist

- [ ] Esperar a que `01_preprocessing.ipynb` esté listo (compartido) o ayudar a armarlo.
- [ ] Crear `02_rnn_AlanOsorio.ipynb`, importar `CharRNN(cell_type='rnn')` desde `src.model`.
- [ ] Entrenar 30–50 épocas, registrar en MLflow con `run_name="RNN_AlanOsorio"`.
- [ ] Reportar en el notebook: loss curves, perplejidad, ejemplo de 5 nombres muestreados.
- [ ] Si tu modelo es el mejor, copiar el checkpoint a `Parte_1_Generador_Caracteres/models/best_model.pt`.

### Hiperparámetros sugeridos

- `embed_dim=32`, `hidden_dim=128`, `num_layers=1`.
- `lr=1e-3` (Adam), `batch_size=64`.
- Early stopping con `patience=5` por val loss.

---

## Parte 4 — Backend Lambda + AWS Infra

Eres el dueño de toda la subcarpeta [Parte_4_Integracion_Web/](../Parte_4_Integracion_Web/) **excepto el frontend** (eso es de Santiago).

### Archivos que vas a crear

- [Parte_4_Integracion_Web/lambda/Dockerfile](../Parte_4_Integracion_Web/lambda/Dockerfile)
- [Parte_4_Integracion_Web/lambda/handler.py](../Parte_4_Integracion_Web/lambda/handler.py) — FastAPI + `mangum.Mangum(app)`.
- [Parte_4_Integracion_Web/lambda/inference.py](../Parte_4_Integracion_Web/lambda/inference.py) — carga `best_model.pt` en memoria global.
- [Parte_4_Integracion_Web/lambda/schemas.py](../Parte_4_Integracion_Web/lambda/schemas.py) — Pydantic.
- [Parte_4_Integracion_Web/lambda/requirements.txt](../Parte_4_Integracion_Web/lambda/requirements.txt) — `torch --index-url ...cpu`, `fastapi`, `mangum`, `requests`.
- [Parte_4_Integracion_Web/lambda/deploy.sh](../Parte_4_Integracion_Web/lambda/deploy.sh) — build + ECR push + `lambda update-function-code`.
- [Parte_4_Integracion_Web/infra/api_gateway.yaml](../Parte_4_Integracion_Web/infra/api_gateway.yaml) — OpenAPI o SAM template.
- [Parte_4_Integracion_Web/infra/lambda_iam_policy.json](../Parte_4_Integracion_Web/infra/lambda_iam_policy.json) — permisos mínimos.

### Checklist

- [ ] Crear repositorio ECR (`aws ecr create-repository --repository-name dino-lab`).
- [ ] Escribir `Dockerfile` basado en `public.ecr.aws/lambda/python:3.11`. **Verificar que el tamaño total < 10 GB** (PyTorch CPU pesa ~600 MB).
- [ ] Implementar los 5 endpoints (`/health`, `/generate`, `/describe`, `/image`, `/new-dinosaur`) con FastAPI.
- [ ] `/describe` y `/image` son proxies a `OLLAMA_NGROK_URL` y `DIFFUSION_NGROK_URL` (env vars).
- [ ] Crear API Gateway REST API, método `ANY` proxy a Lambda, **CORS habilitado**.
- [ ] Configurar Lambda: `timeout=30`, `memory=2048`, env vars con las URLs de ngrok.
- [ ] Habilitar CloudFront delante del bucket S3 que pondrá Santiago.
- [ ] Probar end-to-end: `curl POST /new-dinosaur` debe devolver nombre+descripción+imagen en < 30 s.

### Dependencias de otros

- Necesitas `models/best_model.pt` listo (Parte 1) — coordínate con quien gane el podio entre RNN/LSTM/GRU.
- Necesitas `OLLAMA_NGROK_URL` (Juan Camilo) y `DIFFUSION_NGROK_URL` (Santiago) para configurar la Lambda.

### Coordinaciones críticas

- **Antes de cambiar la firma de un endpoint**: avisar a Santiago (frontend) en el mismo PR.
- **Antes de redeploy**: avisar al equipo, el endpoint queda fuera ~30 s.
- **Si las URLs de ngrok rotan**: ejecutar `aws lambda update-function-configuration --environment Variables={OLLAMA_NGROK_URL=...,DIFFUSION_NGROK_URL=...}`.
