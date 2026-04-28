# Parte 4 — Integración Web (S3 + CloudFront)

Sitio web que integra los tres puntos anteriores. Es **el entregable principal**: la sustentación se hace recorriendo este sitio.

## Arquitectura

```
┌──────────────────────┐
│  Frontend (S3 +      │   fetch() directo a 3 ngrok URLs
│  CloudFront)         │ ───┬─────────┬──────────────┐
└──────────────────────┘    ▼         ▼              ▼
                       ┌────────┐ ┌────────┐  ┌──────────┐
                       │ Ollama │ │Generator│  │Diffusion │
                       │SageMkr │ │SageMkr  │  │ Colab T4 │
                       │ :11434 │ │ :8000   │  │  :8000   │
                       └────────┘ └────────┘  └──────────┘
                            ngrok    ngrok       ngrok
```

**Decisión clave**: el modelo del generador NO se sirve desde Lambda. Se sirve desde la **misma instancia de SageMaker** que aloja Ollama, vía FastAPI + ngrok. Esto simplifica la arquitectura y elimina la complejidad de empacar PyTorch en una imagen de Lambda.

## Entregables

1. **Sitio público** (CloudFront/S3) con tres secciones:
   - **Descripción del modelo**: arquitectura, hiperparámetros, learning curves, métricas (loss/perplejidad por celda).
   - **Sección de ejemplos**: tabla con los 10 nombres + descripciones + imágenes.
   - **Sección interactiva**: botón "Nuevo Dinosaurio" → genera nombre, descripción e imagen en vivo.
2. Configuración de S3 + CloudFront (bucket público, distribución, invalidaciones).

## Estructura

```
Parte_4_Integracion_Web/
└── web/
    ├── index.html          # 3 secciones
    ├── styles.css
    ├── app.js              # fetch directo a las 3 ngrok URLs (sin Lambda)
    ├── config.js           # URLs de ngrok (no commitear con valores reales)
    ├── examples.json       # 10 nombres + descripciones + URLs S3 de imágenes
    └── deploy_s3.sh        # aws s3 sync + cloudfront create-invalidation
```

## Endpoints que consume el frontend

Todos vía ngrok (no AWS API Gateway, no Lambda).

| Endpoint | Origen | Request | Response |
|---|---|---|---|
| `POST /generate` | SageMaker (FastAPI) | `{"temperature":1.0,"top_p":0.9,"top_k":null}` | `{"name":"mangosaurus"}` |
| `POST /api/generate` | SageMaker (Ollama) | prompt paleontológico con el nombre | `{"response":"..."}` |
| `POST /image` | Colab (FastAPI) | `{"name":"...","description":"..."}` | `{"image_url":"..."}` |

El botón "Nuevo Dinosaurio" hace los **3 fetches en cascada** desde el navegador (sin orquestador intermedio). Cada uno puede tardar; el frontend muestra spinner hasta que llega la imagen.

## ¿Por qué CORS funciona?

ngrok responde con headers CORS permisivos por defecto. Si en algún momento se bloqueara, hay que agregar `--response-header-add 'Access-Control-Allow-Origin: *'` al comando ngrok.

## Configuración crítica

- **CloudFront**: TTL bajo (300 s) para que `examples.json` y los assets se actualicen rápido tras un deploy.
- **S3 bucket**: política pública para `*.png` (las imágenes de Colab) y para los archivos del sitio.
- **Las URLs de ngrok rotan cada ~2 h en plan free**: hay que actualizar `web/config.js` y volver a desplegar, o usar el archivo `examples.json` para los ejemplos estáticos (que no dependen de ngrok).

## Cómo desplegar

```bash
# desde la raíz del repo
S3_BUCKET=dino-lab-frontend \
CLOUDFRONT_DISTRIBUTION=E1XXXXXXXXXX \
bash Parte_4_Integracion_Web/web/deploy_s3.sh
```

## Cómo verificar

1. Abrir la URL de CloudFront en el navegador.
2. Sección **Modelo**: ver curvas de aprendizaje y la tabla con métricas reales.
3. Sección **Ejemplos**: ver los 10 dinosaurios generados con sus imágenes.
4. Sección **Interactiva**: click en "Nuevo Dinosaurio" → spinner → en menos de 60 s aparece nombre + descripción + imagen.

Si el botón falla:

- Abrir DevTools → Network → ver cuál fetch tronó.
- Si es `/generate`: la URL de ngrok del generador está caída → revisar SageMaker.
- Si es `/api/generate`: Ollama caído → revisar SageMaker.
- Si es `/image`: Colab caído → reabrir el notebook y reconectar el túnel.
