// URLs públicas de ngrok. Editar y volver a desplegar cuando roten.
// Con plan free de ngrok hay una sola URL — el generador proxea Ollama internamente.

window.DINO_CONFIG = {
  // SageMaker — FastAPI del generador (también proxea /api/generate a Ollama)
  GENERATOR_URL: "https://serpent-secular-distract.ngrok-free.dev",

  // OLLAMA_URL apunta a la misma URL — el FastAPI hace el proxy internamente
  OLLAMA_URL: "https://serpent-secular-distract.ngrok-free.dev",
  OLLAMA_MODEL: "gemma2:2b",

  // Difusión via /image en la misma FastAPI — Pollinations.ai internamente
  DIFFUSION_URL: "https://serpent-secular-distract.ngrok-free.dev",
};
