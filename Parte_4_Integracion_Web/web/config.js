// URLs públicas de ngrok. Editar y volver a desplegar cuando roten.
// NO commitear este archivo con valores reales en producción — usar deploy_s3.sh
// para inyectar via env vars o dejar placeholder en el repo.

window.DINO_CONFIG = {
  // SageMaker — FastAPI del generador (Parte 1)
  GENERATOR_URL: "https://REPLACE_ME.ngrok-free.app",

  // SageMaker — Ollama
  OLLAMA_URL: "https://REPLACE_ME.ngrok-free.app",
  OLLAMA_MODEL: "gemma2:2b",

  // Colab — modelo de difusión
  DIFFUSION_URL: "https://REPLACE_ME.ngrok-free.app",
};
