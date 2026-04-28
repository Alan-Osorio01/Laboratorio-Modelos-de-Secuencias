# Santiago Diaz — Tareas asignadas

## Resumen

Te toca la **variante GRU** del generador, **toda la Parte 3** (modelo de difusión en Colab) y el **frontend** del sitio web (Parte 4). También coordinas el muestreo final que selecciona los 10 nombres oficiales.

## Partes en las que estás involucrado

- **Parte 1** (variante GRU + sampling final): tu notebook personal + el notebook compartido `03_sampling.ipynb`.
- **Parte 3** (text-to-image): owner de toda la sección.
- **Parte 4** (frontend): owner del sitio estático en S3/CloudFront.

---

## Parte 1 — Variante GRU + sampling final

### Archivos que vas a tocar

- [Parte_1_Generador_Caracteres/notebooks/02_gru_SantiagoDiaz.ipynb](../Parte_1_Generador_Caracteres/notebooks/02_gru_SantiagoDiaz.ipynb) — tu notebook (créalo).
- [Parte_1_Generador_Caracteres/notebooks/03_sampling.ipynb](../Parte_1_Generador_Caracteres/notebooks/03_sampling.ipynb) — **compartido**, pero tú lo lideras (te toca seleccionar los 10 finalistas).
- [Parte_1_Generador_Caracteres/src/model.py](../Parte_1_Generador_Caracteres/src/model.py) y [src/sample.py](../Parte_1_Generador_Caracteres/src/sample.py) — colaboras.

### Checklist (variante GRU)

- [ ] Esperar `01_preprocessing.ipynb` listo (compartido).
- [ ] Crear `02_gru_SantiagoDiaz.ipynb`, usar `CharRNN(cell_type='gru')`.
- [ ] Entrenar 30–50 épocas, registrar en MLflow con `run_name="GRU_SantiagoDiaz"`.
- [ ] Reportar: loss curves, perplejidad, ejemplo de 5 nombres muestreados.
- [ ] Si tu modelo es el mejor, copiar el checkpoint a `Parte_1_Generador_Caracteres/models/best_model.pt`.

### Checklist (sampling final — `03_sampling.ipynb`)

- [ ] Cargar el `best_model.pt` (el mejor entre las 3 variantes).
- [ ] Generar nombres con todas las combinaciones: `temperature ∈ {0.7, 1.0, 2.5, 4.0}`, `top_k ∈ {None, 5, 10}`, `top_p ∈ {None, 0.9, 0.95}`.
- [ ] Filtrar nombres que ya están en `dinos.csv` (originalidad).
- [ ] Persistir todo el barrido en `../data/generated/names.csv` con columnas `name, cell_type, temperature, top_k, top_p`.
- [ ] **Seleccionar los 10 mejores** (criterio: plausibilidad fonética + no repetidos + variedad de longitud).
- [ ] Escribir la **nota de 3–5 líneas** comparando temperatura/top-k/top-p en `../reports/sampling_comparison.md`.

---

## Parte 3 — Text-to-Image en Colab

Eres el dueño de toda la subcarpeta [Parte_3_Difusion_Imagenes/](../Parte_3_Difusion_Imagenes/).

### Archivos que vas a crear

- [Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb](../Parte_3_Difusion_Imagenes/notebooks/05_diffusion_images.ipynb) — el notebook que corre en Colab T4.

### Checklist

- [ ] Abrir Colab, runtime **T4 GPU**.
- [ ] Instalar `diffusers transformers torch accelerate safetensors`.
- [ ] Cargar `amused/amused-512` (recomendado) o `stabilityai/sdxl-turbo`.
- [ ] Leer los 10 nombres + descripciones desde `descriptions.json` (te lo pasa Juan Camilo).
- [ ] Generar 10 imágenes a 512×512, `num_inference_steps=12`.
- [ ] Prompt: `"A paleo-illustration of a dinosaur named {name}. {description}. Realistic, museum diorama style, neutral background."`.
- [ ] Guardar como `{name}.png` y subirlas a S3: `aws s3 cp images/ s3://$S3_BUCKET/images/ --recursive`.
- [ ] Si decides exponer la difusión vía ngrok (para el botón "Nuevo Dinosaurio"), levantar túnel y pasarle la URL a **Alan** para la Lambda.

### Dependencias de otros

- Necesitas `descriptions.json` (Juan Camilo, Parte 2).
- Necesitas el `S3_BUCKET` creado por Alan (Parte 4).
- Tu URL de ngrok (si la difusión se sirve en vivo) la consume Alan.

---

## Parte 4 — Frontend del sitio web

### Archivos que vas a crear

- [Parte_4_Integracion_Web/web/index.html](../Parte_4_Integracion_Web/web/index.html) — 3 secciones (modelo, ejemplos, interactiva).
- [Parte_4_Integracion_Web/web/styles.css](../Parte_4_Integracion_Web/web/styles.css)
- [Parte_4_Integracion_Web/web/app.js](../Parte_4_Integracion_Web/web/app.js) — `fetch(API_GATEWAY_URL + "/new-dinosaur")`.
- [Parte_4_Integracion_Web/web/examples.json](../Parte_4_Integracion_Web/web/examples.json) — 10 nombres + descripciones + URLs S3 de imágenes.
- [Parte_4_Integracion_Web/web/deploy_s3.sh](../Parte_4_Integracion_Web/web/deploy_s3.sh) — `aws s3 sync` + `cloudfront create-invalidation`.

### Checklist

- [ ] **Sección 1 — Descripción del modelo**: cargar `learning_curves.png` (de los reports), tabla con hiperparámetros, métricas finales (loss/perplejidad por celda), descripción de la arquitectura.
- [ ] **Sección 2 — Ejemplos**: tabla o grid con los 10 nombres, descripciones cortas y miniaturas de las imágenes.
- [ ] **Sección 3 — Interactiva**: botón "Nuevo Dinosaurio" que:
  - Hace `POST /new-dinosaur` al API Gateway.
  - Muestra spinner mientras espera (puede tardar hasta 30 s).
  - Renderiza nombre + descripción + imagen.
  - Maneja errores (ngrok caído, Lambda timeout).
- [ ] Probar el `examples.json` con datos reales de Parte 1, 2 y 3.
- [ ] Desplegar con `deploy_s3.sh` y verificar en CloudFront.

### Coordinaciones críticas

- **Antes de cambiar la firma del fetch**: avisar a Alan (backend Lambda) en el mismo PR.
- **CORS**: si el navegador rechaza la llamada, es problema del API Gateway (avisar a Alan).
- **Sustentación**: el sitio que tú haces es lo que el profesor va a calificar — pruébalo bien antes del día.
