// URLs públicas de ngrok. Editar y volver a desplegar cuando roten.
// Con plan free de ngrok hay una sola URL — el generador proxea Ollama internamente.

window.DINO_CONFIG = {
  // SageMaker — FastAPI del generador (también proxea /api/generate a Ollama)
  GENERATOR_URL: "https://serpent-secular-distract.ngrok-free.dev",

  // OLLAMA_URL apunta a la misma URL — el FastAPI hace el proxy internamente
  OLLAMA_URL: "https://serpent-secular-distract.ngrok-free.dev",
  OLLAMA_MODEL: "gemma2:2b",

  // Colab — modelo de difusión (pendiente Santiago)
  DIFFUSION_URL: "https://REPLACE_ME.ngrok-free.app",
};
