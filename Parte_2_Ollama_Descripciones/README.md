# Parte 2 — Descripciones con Ollama (SageMaker)

Generar una breve descripción para cada uno de los 10 nombres producidos en la Parte 1, usando un LLM local servido por Ollama. **No se permite usar APIs externas.**

## Entregables

1. Ollama corriendo dentro de Docker en una instancia SageMaker `m5.xlarge`, con persistencia entre apagados.
2. Endpoint público vía ngrok.
3. **10 descripciones** (2–3 frases cada una) coherentes con la nomenclatura paleontológica real, persistidas en `../data/generated/descriptions.json`.

## Estructura

```
Parte_2_Ollama_Descripciones/
├── notebooks/
│   └── 04_ollama_descriptions.ipynb     # corre EN SageMaker, no localmente
└── infra/
    ├── ollama_lifecycle_onstart.sh      # mueve Docker data-root → /SageMaker
    ├── ollama_docker_run.sh             # docker run + ollama pull
    └── ngrok_tunnel.sh                  # expone localhost:11434
```

## Especificaciones

**Persistencia (crítico)**:
- Los notebooks SageMaker solo conservan `/SageMaker/`.
- El lifecycle script `on-start` mueve `Docker data-root` a `/home/ec2-user/SageMaker/docker` antes de cada arranque.
- Ollama monta su volumen en `/home/ec2-user/SageMaker/ollama` para que los modelos descargados sobrevivan al apagado.

**Modelo recomendado** (m5.xlarge es CPU-only, 16 GB RAM):
- `gemma2:2b` o `qwen2.5:3b` — caben holgados y responden rápido en CPU.
- Evitar modelos > 7B en esta instancia.

**Prompt del sistema** (contexto paleontológico):
- Prefijos griegos/latinos: *mega-, micro-, allo-, archae-, cyno-* (forma, tamaño, lugar).
- Sufijos: *-saurus, -raptor, -odon, -venator, -long, -mimus, -ceratops*.
- Pedir 2–3 frases por nombre, en español, con descripción morfológica plausible.

## Cómo correr

```bash
# en SageMaker (terminal del notebook)
bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh
bash Parte_2_Ollama_Descripciones/infra/ngrok_tunnel.sh
# copiar la URL pública → exportar como OLLAMA_NGROK_URL
# abrir notebooks/04_ollama_descriptions.ipynb y ejecutar
```

## ⚠️ No correr localmente

`04_ollama_descriptions.ipynb` requiere Docker + Ollama corriendo en SageMaker. No tiene sentido ejecutarlo en el laptop — fallará por el endpoint local inexistente.
