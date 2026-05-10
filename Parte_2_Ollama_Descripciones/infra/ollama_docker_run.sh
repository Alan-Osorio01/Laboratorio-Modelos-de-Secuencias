#!/usr/bin/env bash
# Levanta Ollama en Docker (puerto 11434) y descarga el modelo gemma2:2b.
# Monta el volumen de modelos en /SageMaker/ollama para que persistan entre reinicios.
#
# Uso (desde la terminal de SageMaker):
#   bash Parte_2_Ollama_Descripciones/infra/ollama_docker_run.sh
#
# Variables de entorno opcionales:
#   OLLAMA_MODEL  — modelo a descargar (default: gemma2:2b)
#   OLLAMA_PORT   — puerto local (default: 11434)

set -euo pipefail

OLLAMA_MODEL="${OLLAMA_MODEL:-gemma2:2b}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_DIR="/home/ec2-user/SageMaker/ollama"
CONTAINER_NAME="ollama"

# Crear directorio de modelos si no existe
mkdir -p "$OLLAMA_DIR"

# Detener contenedor previo si existe
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "→ deteniendo contenedor previo: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" || true
    docker rm   "$CONTAINER_NAME" || true
fi

echo "→ levantando Ollama en :${OLLAMA_PORT}"
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${OLLAMA_PORT}:11434" \
    -v "${OLLAMA_DIR}:/root/.ollama" \
    ollama/ollama

# Esperar a que Ollama esté listo
echo "→ esperando que Ollama inicie..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
        echo "   Ollama listo después de ${i}s"
        break
    fi
    sleep 2
done

# Descargar el modelo
echo "→ descargando modelo: ${OLLAMA_MODEL} (puede tardar varios minutos la primera vez)"
docker exec "$CONTAINER_NAME" ollama pull "$OLLAMA_MODEL"

echo ""
echo "✓ Ollama corriendo en http://localhost:${OLLAMA_PORT}"
echo "  Modelo disponible: ${OLLAMA_MODEL}"
echo ""
echo "Verificar con:"
echo "  curl http://localhost:${OLLAMA_PORT}/api/tags"
echo "  curl -X POST http://localhost:${OLLAMA_PORT}/api/generate \\"
echo "       -d '{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"hola\",\"stream\":false}'"
