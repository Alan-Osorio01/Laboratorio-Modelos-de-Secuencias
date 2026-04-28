# Alan Osorio — Tareas asignadas

## Resumen

Te toca la **variante RNN simple** del generador, **el código del FastAPI que sirve el modelo** (corre en SageMaker), y **el hosting estático en AWS** (S3 + CloudFront).

> **Cambio de arquitectura**: ya no hay Lambda + API Gateway. El generador se expone vía FastAPI dentro de SageMaker (mismo host que Ollama), y el frontend en S3 llama directo a las URLs de ngrok.

## Partes en las que estás involucrado

- **Parte 1** (variante RNN + FastAPI del generador).
- **Parte 4** (hosting frontend en S3 + CloudFront).

---

## Parte 1 — Variante RNN simple

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb](../Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb) — tu notebook (créalo).
- [Parte_1_Generador_Caracteres/src/model.py](../Parte_1_Generador_Caracteres/src/model.py) — colaboras con Juan Camilo y Santiago en la clase `CharRNN(cell_type=...)`.

### Checklist

- [ ] Esperar `01_preprocessing.ipynb` listo (compartido).
- [ ] Crear `02_rnn_AlanOsorio.ipynb`, importar `CharRNN(cell_type='rnn')`.
- [ ] Entrenar 30–50 épocas, registrar en MLflow con `run_name="RNN_AlanOsorio"`.
- [ ] Reportar: loss curves, perplejidad, ejemplo de 5 nombres muestreados.
- [ ] Si tu modelo es el mejor, copiar el checkpoint a `Parte_1_Generador_Caracteres/models/best_model.pt`.

### Hiperparámetros sugeridos

- `embed_dim=32`, `hidden_dim=128`, `num_layers=1`.
- `lr=1e-3` (Adam), `batch_size=64`.
- Early stopping con `patience=5` por val loss.

---

## Parte 1 (cont.) — FastAPI del generador

Eres dueño del código que expone el modelo vía HTTP.

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/api/main.py](../Parte_1_Generador_Caracteres/api/main.py) — ya está el esqueleto. Tu trabajo es endurecerlo.

### Checklist

- [ ] Leer `main.py` y verificar que `/generate` y `/health` funcionen localmente:
  ```bash
  uvicorn Parte_1_Generador_Caracteres.api.main:app --port 8000
  curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' \
       -d '{"n":3,"temperature":1.0,"top_p":0.9}'
  ```
- [ ] Agregar logging estructurado (en `/var/log/dino-api.log`).
- [ ] Validar que CORS responde a OPTIONS preflight desde el dominio de CloudFront.
- [ ] Documentar el contrato del endpoint en el README de Parte 1.
- [ ] Coordinar con **Juan Camilo** la subida del `best_model.pt` a `/home/ec2-user/SageMaker/models/` en la instancia.

---

## Parte 4 — Frontend hosting (S3 + CloudFront)

### Archivos que vas a tocar

- [Parte_4_Integracion_Web/web/deploy_s3.sh](../Parte_4_Integracion_Web/web/deploy_s3.sh) — ya está el script base.
- (Crear) Plantilla CloudFormation/Terraform o pasos manuales documentados para crear: bucket S3 público + distribución CloudFront + (opcional) Route53.

### Checklist

- [ ] Crear bucket S3 (`dino-lab-frontend-<sufijo>`), habilitar static website hosting, política pública para `*.html, *.css, *.js, *.json, *.png`.
- [ ] Crear distribución CloudFront frente al bucket. TTL bajo (300 s) para iterar rápido.
- [ ] Probar `deploy_s3.sh` con `S3_BUCKET=... CLOUDFRONT_DISTRIBUTION=...`.
- [ ] Validar HTTPS (CloudFront default cert), latencia, y que los headers CORS no se rompan al servir el sitio.
- [ ] Documentar en `Parte_4_Integracion_Web/README.md` los IDs/nombres de los recursos AWS creados (en una sección "Recursos provisionados").

### Dependencias de otros

- El **frontend en sí** lo escribe Santiago. Tú solo hosteas.
- Necesitas las URLs de ngrok de **Juan Camilo** (Ollama + generador) y de **Santiago** (difusión Colab) para llenar `web/config.js` antes del deploy.

### Coordinaciones críticas

- **Antes de cambiar la firma del FastAPI** (`/generate`): avisar a Santiago en el mismo PR — el frontend lo consume.
- **Si las URLs de ngrok rotan**: editar `web/config.js` y volver a correr `deploy_s3.sh`.
