# CLAUDE.md — Guía para el equipo

Este archivo le da contexto a Claude Code (y a cualquier compañero nuevo) sobre cómo se organiza, ejecuta y despliega el laboratorio. Léelo antes de pedirle a Claude que toque el repo.

## 1. Sobre el proyecto

Laboratorio de **Modelos de Secuencias** — NLP. Construimos un generador de nombres de dinosaurios a nivel de carácter con RNN/LSTM/GRU y lo integramos con un LLM (Ollama) para descripciones, un modelo de difusión para imágenes, y un sitio web en AWS.

Cuatro entregables:

1. **Generador de caracteres** — RNN/LSTM/GRU autorregresivo, muestreo con temperatura, top-k y top-p.
2. **Descripciones con Ollama** — LLM local en SageMaker, expuesto vía ngrok.
3. **Text-to-Image** — modelo de difusión liviano en Colab T4.
4. **Integración Web** — sitio en S3+CloudFront que llama una Lambda (con `best_model.pt` empacado en container image) que orquesta los tres servicios.

Enunciado: `../Generador de caracteres - Dino.pdf`. Dataset: <https://github.com/jpospinalo/MachineLearning/blob/main/nlp/dinos.csv>.

## 2. Equipo y división

| Integrante | Responsabilidad principal | Detalle |
|---|---|---|
| Alan Osorio | Variante **RNN simple** + infra AWS (Lambda, S3, CloudFront) | [equipo/Alan_Osorio.md](equipo/Alan_Osorio.md) |
| Juan Camilo Gallardo | Variante **LSTM** + Parte 2 (Ollama en SageMaker) | [equipo/Juan_Camilo_Gallardo.md](equipo/Juan_Camilo_Gallardo.md) |
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
├── Parte_1_Generador_Caracteres/      # RNN/LSTM/GRU + sampling
│   ├── README.md
│   ├── notebooks/    # 01_preprocessing, 02_<celda>_<autor>, 03_sampling
│   ├── src/          # dataset, model, train, sample
│   └── models/       # best_model.pt
├── Parte_2_Ollama_Descripciones/      # LLM local en SageMaker
│   ├── README.md
│   ├── notebooks/    # 04_ollama_descriptions
│   └── infra/        # lifecycle, docker_run, ngrok
├── Parte_3_Difusion_Imagenes/         # text-to-image en Colab T4
│   ├── README.md
│   └── notebooks/    # 05_diffusion_images
├── Parte_4_Integracion_Web/           # backend Lambda + frontend S3
│   ├── README.md
│   ├── lambda/       # Dockerfile, handler, inference, schemas, deploy.sh
│   ├── web/          # index.html, styles.css, app.js, examples.json
│   └── infra/        # api_gateway.yaml, lambda_iam_policy.json
└── reports/          # learning_curves.png, sampling_comparison.md, arquitectura
```

## 6. Reglas para Claude Code

Estas reglas se las aplica Claude cuando trabaja en este repo:

- **No tocar `Parte_1_Generador_Caracteres/models/best_model.pt` sin confirmar.** Es un artefacto compartido; sobreescribirlo invalida resultados que ya se reportaron.
- **No regenerar `data/dinos.csv`.** Es la fuente de verdad; si se necesita refrescar, abrir issue primero.
- **No ejecutar `Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb` localmente.** Solo corre en SageMaker (necesita Docker+Ollama). En local fallará y no es un bug.
- **No ejecutar `Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb` localmente.** Solo corre en Colab T4 (necesita GPU). Mismo principio.
- **URLs de ngrok jamás hardcodeadas.** Siempre `os.environ["OLLAMA_NGROK_URL"]` / `os.environ["DIFFUSION_NGROK_URL"]`. Las URLs rotan en cada reinicio del túnel.
- **Antes de cambiar la firma de un endpoint** en `Parte_4_Integracion_Web/lambda/handler.py`, actualizar `Parte_4_Integracion_Web/web/app.js` en el mismo PR — el frontend es el único cliente.
- **Para experimentos**, crear `Parte_X_*/notebooks/0X_experimento_<NombreApellido>.ipynb` en lugar de modificar el de otro integrante.
- **Despliegue Lambda**: nunca correr `Parte_4_Integracion_Web/lambda/deploy.sh` sin avisar al equipo (rota el endpoint en producción durante ~30 s).
- **Cada persona tiene su `equipo/<NombreApellido>.md`** con el detalle de sus tareas — leerlo antes de pedirle a Claude algo de "su" parte.

## 7. Cómo correr cada parte

### Parte 1 — Entrenar y samplear

```bash
python -m Parte_1_Generador_Caracteres.src.train --cell lstm --epochs 50
python -m Parte_1_Generador_Caracteres.src.sample \
    --checkpoint Parte_1_Generador_Caracteres/models/best_model.pt \
    --n 10 --temperature 1.0 --top-p 0.9
```

### Parte 2 — Ollama en SageMaker

1. Crear notebook SageMaker `m5.xlarge`. Pegar `Parte_2_Ollama_Descripciones/infra/ollama_lifecycle_onstart.sh` como lifecycle config `on-start`.
2. Terminal de SageMaker: `bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh`.
3. `bash Parte_2_Ollama_Descripciones/infra/ngrok_tunnel.sh` → copiar URL pública.
4. Setear `OLLAMA_NGROK_URL`, abrir `Parte_2_Ollama_Descripciones/notebooks/04_ollama_descriptions.ipynb`.

### Parte 3 — Difusión en Colab

1. Abrir `Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb` en Colab, runtime T4.
2. Ejecutar todo. Las 10 imágenes quedan en el filesystem del Colab.
3. Subirlas a S3: `aws s3 cp images/ s3://$S3_BUCKET/images/ --recursive`.

### Parte 4 — Desplegar

```bash
bash Parte_4_Integracion_Web/lambda/deploy.sh   # backend
bash Parte_4_Integracion_Web/web/deploy_s3.sh   # frontend
```

## 8. Endpoints y contratos

API Gateway → Lambda. Todos JSON, todos POST salvo `/health`.

| Endpoint | Request | Response |
|---|---|---|
| `GET /health` | — | `{"status": "ok"}` |
| `POST /generate` | `{"temperature": 1.0, "top_p": 0.9, "top_k": null}` | `{"name": "mangosaurus"}` |
| `POST /describe` | `{"name": "mangosaurus"}` | `{"name": "mangosaurus", "description": "..."}` |
| `POST /image` | `{"name": "mangosaurus", "description": "..."}` | `{"image_url": "https://.../mangosaurus.png"}` |
| `POST /new-dinosaur` | `{}` | `{"name": ..., "description": ..., "image_url": ...}` |

Schemas estrictos en `lambda/schemas.py` — si Claude propone cambiarlos, asegurarse de actualizar también `web/app.js`.

## 9. Troubleshooting

**Ollama no arranca al reiniciar el notebook SageMaker**
→ El lifecycle script falló silenciosamente. Revisar `/var/log/jupyter.log`. Lo más común: la ruta `/home/ec2-user/SageMaker/docker` no existe. Crearla manualmente y re-ejecutar el lifecycle.

**ngrok devuelve 502**
→ El túnel se cayó (las URLs gratis duran ~2 h). Re-ejecutar `infra/ngrok_tunnel.sh`, copiar nueva URL, y actualizar la env var de la Lambda con `aws lambda update-function-configuration --function-name dino-lab --environment Variables={OLLAMA_NGROK_URL=...}`.

**Lambda da timeout en `/new-dinosaur`**
→ Límite duro de API Gateway = 29 s. Si la difusión en Colab tarda más, reducir `num_inference_steps` o cambiar a respuesta async (encolar en SQS y polling desde el frontend).

**`models/best_model.pt` no carga en Lambda**
→ Asegurarse de que `Dockerfile` haga `COPY models/best_model.pt /var/task/`. Verificar con `docker run --rm <image> ls -la /var/task/`.

**Generación produce nombres con `<PAD>` o caracteres raros**
→ Falló el filtrado en `src/sample.py`. Confirmar que `PAD_ID`, `SOS_ID`, `EOS_ID` se excluyen del muestreo y que se corta al primer `<EOS>`.

---

Si vas a pedirle a Claude algo que no encaja en lo anterior, dale el contexto explícitamente. Este archivo cubre lo común; lo raro hay que conversarlo.
