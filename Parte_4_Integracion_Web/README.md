# Parte 4 — Integración Web (AWS Lambda + API Gateway + S3)

Sitio web que integra los tres puntos anteriores. Es **el entregable principal**: la sustentación se hace recorriendo este sitio.

## Entregables

1. **Sitio público** (CloudFront/S3) con tres secciones:
   - **Descripción del modelo**: arquitectura, hiperparámetros, learning curves, métricas (loss/perplejidad por celda).
   - **Sección de ejemplos**: tabla con los 10 nombres + descripciones + imágenes.
   - **Sección interactiva**: botón "Nuevo Dinosaurio" → genera nombre, descripción e imagen en vivo.
2. **Backend Lambda** (container image en ECR) con `best_model.pt` empacado.
3. **API Gateway** con CORS habilitado.
4. Endpoints de Ollama y difusión expuestos vía ngrok (no van en AWS).

## Estructura

```
Parte_4_Integracion_Web/
├── lambda/
│   ├── Dockerfile          # base public.ecr.aws/lambda/python:3.11 + torch CPU + best_model.pt
│   ├── handler.py          # FastAPI + Mangum
│   ├── inference.py        # carga best_model.pt + sample
│   ├── schemas.py          # Pydantic
│   ├── requirements.txt
│   └── deploy.sh           # docker build + ECR push + lambda update-function-code
├── web/
│   ├── index.html          # 3 secciones
│   ├── styles.css
│   ├── app.js              # fetch(API_GATEWAY_URL + "/new-dinosaur")
│   ├── examples.json       # 10 nombres + descripciones + URLs de imágenes
│   └── deploy_s3.sh        # aws s3 sync + create-invalidation
└── infra/
    ├── api_gateway.yaml    # OpenAPI/SAM template
    └── lambda_iam_policy.json  # solo logs CloudWatch
```

## Endpoints

| Endpoint | Request | Response |
|---|---|---|
| `GET /health` | — | `{"status": "ok"}` |
| `POST /generate` | `{"temperature": 1.0, "top_p": 0.9, "top_k": null}` | `{"name": "mangosaurus"}` |
| `POST /describe` | `{"name": "mangosaurus"}` | `{"name": ..., "description": ...}` |
| `POST /image` | `{"name": ..., "description": ...}` | `{"image_url": "https://.../mangosaurus.png"}` |
| `POST /new-dinosaur` | `{}` | `{"name": ..., "description": ..., "image_url": ...}` |

## Configuración crítica

- **Lambda timeout**: 30 s (el límite duro de API Gateway es 29 s).
- **Lambda memory**: 2048 MB (mejora notablemente el throughput de PyTorch en CPU).
- **CORS**: habilitado en API Gateway para que el frontend (S3/CloudFront) pueda llamar.
- **URLs de ngrok**: viven como variables de entorno de la Lambda (`OLLAMA_NGROK_URL`, `DIFFUSION_NGROK_URL`). Rotan al reiniciar los túneles → actualizar con `aws lambda update-function-configuration`.

## Cómo desplegar

```bash
# backend
bash Parte_4_Integracion_Web/lambda/deploy.sh

# frontend
bash Parte_4_Integracion_Web/web/deploy_s3.sh
```

## Cómo verificar

```bash
# health check
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/health

# end-to-end
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/new-dinosaur \
     -H "Content-Type: application/json" -d '{}'
```

Después abrir la URL de CloudFront, click en "Nuevo Dinosaurio" → debe ver nombre + descripción + imagen en menos de 30 s.
