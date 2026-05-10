// Frontend del Lab — llama directamente a las 3 ngrok URLs (sin Lambda intermedio).
// Las URLs viven en config.js (editar y redesplegar cuando roten).

const CFG = window.DINO_CONFIG || {};

const PALEO_PROMPT = (name) => `
Eres un paleontólogo experto. Describe en 4 a 5 frases en español el dinosaurio
ficticio llamado "${name}". Incluye: período geológico, región donde vivió,
dieta, características físicas distintivas (tamaño, rasgos únicos) y un dato
curioso sobre su comportamiento o adaptación. Usa terminología paleontológica
real. No uses listas, solo prosa fluida.
`.trim();

// ============================================================
// Sección de ejemplos
// ============================================================
async function loadExamples() {
  const grid = document.getElementById("examples-grid");
  try {
    const res = await fetch("examples.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const items = await res.json();
    grid.innerHTML = "";
    if (!items.length) {
      grid.innerHTML = `<p class="muted">examples.json está vacío. Llénalo con los 10 nombres reales tras correr las Partes 1–3.</p>`;
      return;
    }
    for (const item of items) {
      const node = document.createElement("div");
      node.className = "item";
      node.innerHTML = `
        <img src="${item.image_url}" alt="${item.name}"
             onerror="this.style.background='#222';this.removeAttribute('src');" />
        <div class="body">
          <h4>${item.name}</h4>
          <p>${item.description ?? ""}</p>
        </div>`;
      grid.appendChild(node);
    }
  } catch (err) {
    grid.innerHTML = `<p class="error">No se pudo cargar examples.json: ${err.message}</p>`;
  }
}

// ============================================================
// Llamadas individuales a cada ngrok
// ============================================================
async function fetchName() {
  const res = await fetch(`${CFG.GENERATOR_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n: 1, temperature: 1.0, top_p: 0.9 }),
  });
  if (!res.ok) throw new Error(`generador: HTTP ${res.status}`);
  const data = await res.json();
  return data.names[0];
}

async function fetchDescription(name) {
  const res = await fetch(`${CFG.OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: CFG.OLLAMA_MODEL,
      prompt: PALEO_PROMPT(name),
      stream: false,
    }),
  });
  if (!res.ok) throw new Error(`ollama: HTTP ${res.status}`);
  const data = await res.json();
  return (data.response || "").trim().replace(/\*/g, "");
}

async function fetchImage(name, description) {
  const res = await fetch(`${CFG.DIFFUSION_URL}/image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error(`difusión: HTTP ${res.status}`);
  const data = await res.json();
  return data.image_url;
}

// ============================================================
// Botón "Nuevo Dinosaurio" — orquesta los 3 fetches
// ============================================================
async function newDinosaur() {
  const btn = document.getElementById("new-dino-btn");
  const result = document.getElementById("result");
  const errBox = document.getElementById("result-error");
  const status = document.getElementById("status");

  btn.disabled = true;
  result.classList.add("hidden");
  errBox.classList.add("hidden");
  status.textContent = "";

  try {
    btn.textContent = "Generando nombre…";
    status.textContent = "1/3 — invocando el generador (SageMaker)";
    const name = await fetchName();
    document.getElementById("result-name").textContent = name;

    btn.textContent = "Generando descripción…";
    status.textContent = "2/3 — pidiendo descripción a Ollama";
    const description = await fetchDescription(name);
    document.getElementById("result-description").textContent = description;
    result.classList.remove("hidden");

    btn.textContent = "Generando imagen…";
    status.textContent = "3/3 — generando imagen con difusión";
    const image_url = await fetchImage(name, description);
    const img = document.getElementById("result-image");
    img.src = image_url;
    img.alt = name;
    img.style.display = "block";

    status.textContent = "✓ listo";
  } catch (err) {
    errBox.textContent = `Error: ${err.message}`;
    errBox.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "🦕 Generar nuevo dinosaurio";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
  document.getElementById("new-dino-btn").addEventListener("click", newDinosaur);
});
