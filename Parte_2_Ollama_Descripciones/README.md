# Parte 2 — SageMaker (Ollama + Generador) con ngrok

La instancia de SageMaker es el **núcleo del backend en AWS**. Aloja **dos servicios**:

1. **Ollama** (Docker) — sirve un LLM local para las descripciones paleontológicas.
2. **Generador de caracteres** (FastAPI) — expone el `best_model.pt` de la Parte 1 con `/generate`.

Ambos se exponen al exterior mediante **ngrok**. Las URLs públicas las consume el frontend de la Parte 4 directamente.

## Especificaciones de la instancia

| Item | Valor |
|---|---|
| Tipo de instancia | `m5.xlarge` (CPU, 4 vCPU, 16 GB RAM) |
| **Volumen EBS** | **mínimo 100 GB** (para Docker data-root + modelos Ollama + checkpoint del generador) |
| Sistema base | Amazon Linux 2 (default SageMaker) |
| Persistencia | Solo `/home/ec2-user/SageMaker/` sobrevive entre apagados |

## Entregables

1. Lifecycle script `on-start` que mueve Docker data-root a `/SageMaker/docker` (persistente).
2. Ollama corriendo en Docker, modelo descargado en `/SageMaker/ollama/`.
3. **FastAPI del generador** corriendo en el host (uvicorn) o en otro contenedor.
4. **Dos túneles ngrok** activos (uno para Ollama `:11434`, uno para el generador `:8000`).
5. **10 descripciones** generadas y guardadas en `../data/generated/descriptions.json`.

## Estructura

```
Parte_2_Ollama_Descripciones/
├── notebooks/
│   └── 04_ollama_descriptions.ipynb     # corre EN SageMaker, no localmente
└── infra/
    ├── ollama_lifecycle_onstart.sh      # mueve Docker data-root → /SageMaker
    ├── ollama_docker_run.sh             # docker run + ollama pull
    ├── start_generator_api.sh           # uvicorn de Parte_1/api/main.py
    └── ngrok_tunnels.sh                 # levanta los DOS túneles
```

> El código del generador FastAPI vive en [`../Parte_1_Generador_Caracteres/api/main.py`](../Parte_1_Generador_Caracteres/api/main.py) — esa parte la mantiene Alan. Aquí solo lo lanzamos.

## Persistencia (crítico)

- Los notebooks SageMaker solo conservan `/SageMaker/`.
- El lifecycle `on-start` (no `on-create`) mueve `Docker data-root` a `/home/ec2-user/SageMaker/docker` antes de cada arranque.
- Ollama monta su volumen en `/home/ec2-user/SageMaker/ollama` para que los modelos descargados sobrevivan al apagado.
- El `best_model.pt` se sube a `/home/ec2-user/SageMaker/models/` (también persiste).

## Modelos recomendados para Ollama

`m5.xlarge` es CPU-only, 16 GB RAM. Caben sin problema:

- `gemma2:2b` — rápido, buenas descripciones cortas.
- `qwen2.5:3b` — un poco más largo de respuesta, calidad ligeramente superior.

**Evitar** modelos > 7B en esta instancia. Con 100 GB de disco caben varios modelos pulled simultáneamente.

## Endpoints expuestos vía ngrok

| Servicio | Puerto local | URL pública |
|---|---|---|
| Ollama | `:11434` | `OLLAMA_NGROK_URL` |
| Generador (FastAPI) | `:8000` | `GENERATOR_NGROK_URL` |

Ambos los consume el frontend de la Parte 4.

## Cómo correr

```bash
# 1. Crear notebook SageMaker m5.xlarge con volumen 100 GB.
# 2. Pegar ollama_lifecycle_onstart.sh como lifecycle config on-start.
# 3. En la terminal de SageMaker:
bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh
bash Parte_2_Ollama_Descripciones/infra/start_generator_api.sh
bash Parte_2_Ollama_Descripciones/infra/ngrok_tunnels.sh
# Copiar las dos URLs públicas → pasarlas al frontend (config.js).
# 4. Abrir notebooks/04_ollama_descriptions.ipynb y ejecutar.
```

## ⚠️ No correr localmente

`04_ollama_descriptions.ipynb` requiere Docker + Ollama corriendo en SageMaker. No tiene sentido ejecutarlo en el laptop — fallará por el endpoint local inexistente.
