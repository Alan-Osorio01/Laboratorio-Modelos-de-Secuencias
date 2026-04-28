# Parte 3 — Text-to-Image (Colab)

Generar una imagen para cada uno de los 10 nombres, usando un modelo de difusión liviano que pueda correr en Colab T4.

## Entregables

1. **10 imágenes** (una por nombre), guardadas en `../data/generated/images/{name}.png`.
2. Subida de imágenes a S3 para que el frontend (Parte 4) las consuma.

## Estructura

```
Parte_3_Difusion_Imagenes/
└── notebooks/
    └── 05_diffusion_images.ipynb   # corre EN Colab T4, no localmente
```

## Especificaciones

**Entorno**:
- Google Colab con runtime **T4 GPU**.
- Instalar: `diffusers transformers torch accelerate safetensors`.

**Modelo recomendado**:
- `amused/amused-512` — liviano, rápido (12 pasos de inferencia bastan).
- Alternativa: `stabilityai/sdxl-turbo` con `num_inference_steps=1`.

**Generación**:
- Resolución `512x512` (limitar para reducir consumo).
- `num_inference_steps=12`, `guidance_scale=7.5`.
- Prompt: usar el **nombre + la descripción de Ollama** (Parte 2):
  ```
  A paleo-illustration of a dinosaur named {name}.
  {description}.
  Realistic, museum diorama style, neutral background.
  ```

**Salida**:
- Guardar las 10 PNG con el nombre del dinosaurio.
- `aws s3 cp images/ s3://$S3_BUCKET/images/ --recursive` (las URLs van al `examples.json` del frontend).

## Cómo correr

1. Abrir `notebooks/05_diffusion_images.ipynb` en Colab.
2. Runtime → Change runtime type → T4 GPU.
3. Subir `../data/generated/descriptions.json` o pegarlo en una celda.
4. Ejecutar todo. Las imágenes se descargan al final como ZIP.

## ⚠️ No correr localmente

Sin GPU el modelo de difusión tarda demasiado por imagen. Solo Colab T4 (o equivalente).
