# Resumen del proyecto — Isla de los Dinosaurios

## ¿Qué hicimos?

Construimos un sistema completo que genera nombres de dinosaurios, les crea una descripción y produce una imagen, todo integrado en un sitio web.

El flujo cuando alguien pulsa el botón es:
1. Un modelo de redes neuronales genera un nombre nuevo
2. Un LLM local describe al dinosaurio
3. Un modelo de difusión genera la imagen
4. Todo aparece en el sitio web

---

## Las 4 partes

### Parte 1 — El generador de nombres
Entrenamos una red neuronal recurrente (CharRNN) con 1 536 nombres reales de dinosaurios. El modelo aprende los patrones de los nombres carácter por carácter y genera nombres nuevos que suenan plausibles.

Probamos tres tipos de celda:
| Celda | Val Loss | Perplejidad |
|---|---|---|
| RNN | 1.4908 | 4.44 |
| LSTM | 1.4853 | 4.42 |
| **GRU ✓** | **1.4774** | **4.38** |

Ganó **GRU** — quedó como el modelo en producción.

Para controlar la creatividad usamos tres parámetros:
- **Temperatura**: alta = más creativo, baja = más predecible. Usamos `T=1.0`.
- **top-k**: solo considera los k caracteres más probables en cada paso.
- **top-p (nucleus)**: acumula probabilidad hasta p. Usamos `top_p=0.9`.

### Parte 2 — Descripciones con Ollama
Instalamos **Ollama** (gemma2:2b) en Docker dentro de una instancia SageMaker m5.xlarge en AWS. El modelo corre completamente local, sin APIs externas.

Para que el sitio web pueda llamarlo, lo exponemos con **ngrok** (túnel HTTP público).

### Parte 3 — Imágenes con difusión
Usamos el modelo `amused/amused-512` de Hugging Face en Google Colab con GPU T4. El prompt combina el nombre + la descripción de Ollama para generar la imagen.

### Parte 4 — Sitio web
El sitio está desplegado en **AWS S3** como sitio estático. Tiene tres secciones:
- **Modelo**: arquitectura, métricas, curvas de aprendizaje
- **Ejemplos**: los 10 dinosaurios con nombre, descripción e imagen
- **Nuevo dinosaurio**: botón que genera todo en vivo

---

## Endpoints reales (mientras SageMaker esté activo)

**Base URL:** `https://serpent-secular-distract.ngrok-free.dev`

| ¿Qué hace? | Método | Endpoint | Body |
|---|---|---|---|
| Generar nombre | POST | `/generate` | `{"n":1,"temperature":1.0,"top_p":0.9}` |
| Generar descripción | POST | `/api/generate` | `{"model":"gemma2:2b","prompt":"...","stream":false}` |
| Generar imagen | POST | `/image` | `{"name":"...","description":"..."}` |
| Estado de la API | GET | `/health` | — |

**Ejemplo real para generar un nombre:**
```bash
curl -X POST https://serpent-secular-distract.ngrok-free.dev/generate \
  -H "Content-Type: application/json" \
  -d '{"n":1,"temperature":1.0,"top_p":0.9}'
```

**Sitio web:** http://frontend-dino-lab.s3-website-us-east-1.amazonaws.com

---

## Arquitectura resumida

```
Navegador (S3)
    │
    ├── POST /generate      →  FastAPI (SageMaker) → CharRNN (GRU)
    ├── POST /api/generate  →  FastAPI (SageMaker) → Ollama (gemma2:2b, Docker)
    └── POST /image         →  FastAPI (SageMaker) → Pollinations.ai
                                        ↑
                              ngrok (serpent-secular-distract.ngrok-free.dev)
```

Un solo túnel ngrok cubre los tres servicios porque el FastAPI actúa como intermediario.

---

## Preguntas frecuentes

**¿Por qué GRU ganó sobre LSTM?**
GRU tiene menos parámetros que LSTM (no tiene celda de memoria separada) y en datasets pequeños como el nuestro eso ayuda a no sobreajustar.

**¿Por qué top-p y no top-k?**
top-p adapta cuántos caracteres considera en cada paso según la distribución real. top-k es fijo y a veces corta opciones válidas o incluye basura.

**¿Por qué un solo ngrok para todo?**
El plan gratuito de ngrok solo permite un túnel activo. La solución fue agregar `/api/generate` e `/image` directamente al FastAPI del generador, que internamente redirige a Ollama y a Pollinations.

**¿Dónde está el modelo guardado?**
En `Parte_1_Generador_Caracteres/models/best_model.pt` (GRU). También están los checkpoints individuales de RNN, LSTM y GRU.

**¿Cómo se persiste Ollama entre reinicios de SageMaker?**
Movimos el Docker data-root a `/SageMaker/docker`, que vive en el volumen EBS. Con un lifecycle script on-start esto se reconfigura automáticamente al encender la instancia.
