# CLAUDE.md — Guía para el equipo

Este archivo le da contexto a Claude Code (y a cualquier compañero nuevo) sobre cómo se organiza, ejecuta y despliega el laboratorio. Léelo antes de pedirle a Claude que toque el repo.

## 1. Sobre el proyecto

Laboratorio de **Modelos de Secuencias** — NLP. Construimos un generador de nombres de dinosaurios a nivel de carácter con RNN/LSTM/GRU y lo integramos con un LLM (Ollama) para descripciones, un modelo de difusión para imágenes, y un sitio web en AWS.

Cuatro entregables:

1. **Generador de caracteres** — RNN/LSTM/GRU autorregresivo, muestreo con temperatura, top-k y top-p.
2. **Descripciones con Ollama** — LLM local en SageMaker (Docker), expuesto vía ngrok.
3. **Text-to-Image** — modelo de difusión liviano en Colab T4, expuesto vía ngrok.
4. **Integración Web** — sitio en S3+CloudFront que llama directo a las 3 URLs de ngrok (sin Lambda intermedio).

> **Arquitectura clave**: la **misma instancia SageMaker** sirve Ollama Y el generador de la Parte 1 (FastAPI). Ambos detrás de ngrok. Volumen EBS **mínimo 100 GB** para acomodar Docker data-root + modelos Ollama + checkpoint del generador.

Enunciado: `../Generador de caracteres - Dino.pdf`. Dataset: <https://github.com/jpospinalo/MachineLearning/blob/main/nlp/dinos.csv>.

## 2. Equipo y división

| Integrante | Responsabilidad principal | Detalle |
|---|---|---|
| Alan Osorio | Variante **RNN** + FastAPI del generador + infra AWS (S3, CloudFront) | [equipo/Alan_Osorio.md](equipo/Alan_Osorio.md) |
| Juan Camilo Gallardo | Variante **LSTM** + SageMaker (Ollama + generador + ngrok) | [equipo/Juan_Camilo_Gallardo.md](equipo/Juan_Camilo_Gallardo.md) |
| Santiago Diaz | Variante **GRU** + Parte 3 (difusión Colab) + frontend | [equipo/Santiago_Diaz.md](equipo/Santiago_Diaz.md) |

El preprocesamiento (`01_preprocessing.ipynb`), el sampling final (`03_sampling.ipynb`) y `Parte_1_Generador_Caracteres/src/` son **compartidos** — coordinen antes de reescribir.

## 3. Convenciones

### Notebooks
- Nombre: `NN_descripcion_NombreApellido.ipynb` para variantes individuales, `NN_descripcion.ipynb` para los compartidos.
- **Nunca commitear outputs**: usar `nbstripout --install` una vez por clon.
- Las celdas que cargan datos pesados deben envolverse en `if not os.path.exists(...): download(...)`.

### Python
- `black` + `isort` antes de commitear (`black src/ lambda/ && isort src/ lambda/`).
- Type hints en `src/` y `lambda/`. En notebooks no son obligatorios.
- Nada de prints sueltos en `src/`: usar `logging`.

### Git
- Branch por integrante: `alan/<feature>`, `juancamilo/<feature>`, `santiago/<feature>`.
- Merge a `main` por **PR con revisión de al menos otro integrante**. No push directo a main.
- Mensajes en español, presente, conventional-commits ligero: `feat:`, `fix:`, `docs:`, `exp:` (para experimentos), `infra:`.

### Artefactos pesados
- `data/dinos.csv` se versiona (es chico).
- `models/best_model.pt` se versiona con Git LFS si supera 50 MB; si no, commit directo.
- `data/generated/images/*.png` **no se versionan** — viven en S3 (ver `.gitignore`).

## 4. Setup local

```bash
git clone git@github.com:Alan-Osorio01/Laboratorio-Modelos-de-Secuencias.git
cd Laboratorio-Modelos-de-Secuencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nbstripout --install
```

Variables de entorno (crear `.env` localmente, **no commitear**):

```
OLLAMA_NGROK_URL=https://<algo>.ngrok-free.app
DIFFUSION_NGROK_URL=https://<algo>.ngrok-free.app
API_GATEWAY_URL=https://<id>.execute-api.us-east-1.amazonaws.com/prod
S3_BUCKET=dino-lab-frontend-<sufijo>
```

## 5. Mapa del directorio

El repo está organizado **por entregable**. Cada `Parte_X/` tiene su propio README con las especificaciones de esa parte.

```
.
├── CLAUDE.md
├── README.md
├── requirements.txt
├── data/                              # dinos.csv + generated/ (compartido entre partes)
├── equipo/
│   ├── Alan_Osorio.md                 # qué le toca a cada uno
│   ├── Juan_Camilo_Gallardo.md
│   └── Santiago_Diaz.md
├── Parte_1_Generador_Caracteres/      # RNN/LSTM/GRU + sampling + FastAPI del generador
│   ├── README.md
│   ├── notebooks/    # 01_preprocessing, 02_<celda>_<autor>, 03_sampling
│   ├── src/          # dataset, model, train, sample (núcleo PyTorch)
│   ├── api/          # main.py — FastAPI que sirve /generate desde SageMaker
│   └── models/       # best_model.pt
├── Parte_2_Ollama_Descripciones/      # SageMaker: Ollama + generator API + ngrok
│   ├── README.md
│   ├── notebooks/    # 04_ollama_descriptions
│   └── infra/        # lifecycle, docker_run, start_generator_api, ngrok_tunnels
├── Parte_3_Difusion_Imagenes/         # text-to-image en Colab T4
│   ├── README.md
│   └── notebooks/    # 05_diffusion_images
├── Parte_4_Integracion_Web/           # frontend en S3 + CloudFront (sin Lambda)
│   ├── README.md
│   └── web/          # index.html, styles.css, app.js, config.js, examples.json, deploy_s3.sh
└── reports/          # learning_curves.png, sampling_comparison.md, arquitectura
```

## 6. Reglas para Claude Code

Estas reglas se las aplica Claude cuando trabaja en este repo:

- **No tocar `Parte_1_Generador_Caracteres/models/best_model.pt` sin confirmar.** Es un artefacto compartido; sobreescribirlo invalida resultados que ya se reportaron.
- **No regenerar `data/dinos.csv`.** Es la fuente de verdad; si se necesita refrescar, abrir issue primero.
- **No ejecutar `Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb` localmente.** Solo corre en SageMaker (necesita Docker+Ollama). En local fallará y no es un bug.
- **No ejecutar `Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb` localmente.** Solo corre en Colab T4 (necesita GPU). Mismo principio.
- **URLs de ngrok jamás hardcodeadas en código Python.** En el frontend viven en [web/config.js](Parte_4_Integracion_Web/web/config.js); ese archivo se edita y se redespliega cuando los túneles rotan (~2 h en plan free).
- **Antes de cambiar la firma de un endpoint** en [Parte_1_Generador_Caracteres/api/main.py](Parte_1_Generador_Caracteres/api/main.py), actualizar [Parte_4_Integracion_Web/web/app.js](Parte_4_Integracion_Web/web/app.js) en el mismo PR — el frontend es el único cliente.
- **Para experimentos**, crear `Parte_X_*/notebooks/0X_experimento_<NombreApellido>.ipynb` en lugar de modificar el de otro integrante.
- **Volumen EBS de SageMaker = mínimo 100 GB.** Docker data-root + modelos Ollama + checkpoint del generador no caben con menos.
- **Cada persona tiene su `equipo/<NombreApellido>.md`** con el detalle de sus tareas — leerlo antes de pedirle a Claude algo de "su" parte.

## 7. Cómo correr cada parte

### Parte 1 — Entrenar y samplear

```bash
python -m Parte_1_Generador_Caracteres.src.train --cell lstm --epochs 50
python -m Parte_1_Generador_Caracteres.src.sample \
    --checkpoint Parte_1_Generador_Caracteres/models/best_model.pt \
    --n 10 --temperature 1.0 --top-p 0.9
```

### Parte 2 — SageMaker: Ollama + Generator API

1. Crear notebook SageMaker `m5.xlarge` con **volumen EBS de mínimo 100 GB**. Pegar `Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh` como lifecycle config `on-start`.
2. Terminal de SageMaker:
   ```bash
   bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh      # Ollama en :11434
   bash Parte_2_Ollama_Descripciones/infra/start_generator_api.sh    # FastAPI en :8000
   bash Parte_2_Ollama_Descripciones/infra/ngrok_tunnels.sh          # ambos túneles
   ```
3. Copiar las dos URLs públicas → pegarlas en `Parte_4_Integracion_Web/web/config.js`.
4. Abrir `Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb` y ejecutar.

### Parte 3 — Difusión en Colab

1. Abrir `Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb` en Colab, runtime T4.
2. Ejecutar todo. Las 10 imágenes quedan en el filesystem del Colab.
3. Subirlas a S3: `aws s3 cp images/ s3://$S3_BUCKET/images/ --recursive`.

### Parte 4 — Desplegar

```bash
# 1. Editar Parte_4_Integracion_Web/web/config.js con las URLs de ngrok actuales
# 2. Sincronizar a S3 + invalidar CloudFront
S3_BUCKET=dino-lab-frontend bash Parte_4_Integracion_Web/web/deploy_s3.sh
```

No hay backend AWS propio — el frontend en S3 llama directo a las URLs de ngrok del SageMaker (Ollama + generador) y de Colab (difusión).

## 8. Endpoints y contratos

El frontend llama **directamente** a tres servicios distintos vía ngrok. No hay capa intermedia.

| Servicio | Origen | Endpoint | Request | Response |
|---|---|---|---|---|
| Generador | SageMaker (FastAPI, [Parte_1/api/main.py](Parte_1_Generador_Caracteres/api/main.py)) | `POST /generate` | `{"n":1,"temperature":1.0,"top_p":0.9}` | `{"names":["..."]}` |
| Ollama | SageMaker (Docker) | `POST /api/generate` | `{"model":"gemma2:2b","prompt":"...","stream":false}` | `{"response":"..."}` |
| Difusión | Colab T4 (FastAPI dentro del notebook) | `POST /image` | `{"name":"...","description":"..."}` | `{"image_url":"..."}` |

El botón "Nuevo Dinosaurio" del sitio orquesta los 3 fetches en cascada desde el navegador.

## 9. Troubleshooting

**Ollama no arranca al reiniciar el notebook SageMaker**
→ El lifecycle script falló silenciosamente. Revisar `/var/log/jupyter.log`. Lo más común: la ruta `/home/ec2-user/SageMaker/docker` no existe. Crearla manualmente y re-ejecutar el lifecycle.

**ngrok devuelve 502**
→ El túnel se cayó (las URLs gratis duran ~2 h). Re-ejecutar `infra/ngrok_tunnel.sh`, copiar nueva URL, y actualizar la env var de la Lambda con `aws lambda update-function-configuration --function-name dino-lab --environment Variables={OLLAMA_NGROK_URL=...}`.

**El generador FastAPI no arranca en SageMaker**
→ Verificar que `best_model.pt` esté en `/home/ec2-user/SageMaker/models/`. Revisar `/home/ec2-user/SageMaker/logs/generator_api.log`. Si dice ImportError, instalar deps: `pip install -r requirements.txt`.

**Disco lleno en SageMaker**
→ El volumen debe ser **mínimo 100 GB**. Si se está lleno: `docker system prune -a` para liberar imágenes y capas viejas. Confirmar que Docker data-root sigue apuntando a `/SageMaker/docker` con `docker info | grep "Docker Root Dir"`.

**Generación produce nombres con `<PAD>` o caracteres raros**
→ Falló el filtrado en `src/sample.py`. Confirmar que `PAD_ID`, `SOS_ID`, `EOS_ID` se excluyen del muestreo y que se corta al primer `<EOS>`.

---

Si vas a pedirle a Claude algo que no encaja en lo anterior, dale el contexto explícitamente. Este archivo cubre lo común; lo raro hay que conversarlo.
