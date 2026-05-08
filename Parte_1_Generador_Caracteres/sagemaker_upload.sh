#!/usr/bin/env bash
# Empaqueta los archivos mínimos para correr 02_rnn_AlanOsorio.ipynb en SageMaker.
#
# Crea un zip listo para subir al file browser de SageMaker.
# Una vez descomprimido en SageMaker, ejecutar el notebook desde la raíz del zip.
#
# Uso (desde la raíz del repo):
#   bash Parte_1_Generador_Caracteres/sagemaker_upload.sh
#
# Resultado:
#   sagemaker_rnn_package.zip   ← subir este archivo a SageMaker

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/sagemaker_rnn_package.zip"

# Limpiar zip anterior si existe
rm -f "$OUT"

cd "$REPO_ROOT"

zip -r "$OUT" \
  CLAUDE.md \
  data/dinos.csv \
  reports/ \
  Parte_1_Generador_Caracteres/__init__.py \
  Parte_1_Generador_Caracteres/src/__init__.py \
  Parte_1_Generador_Caracteres/src/dataset.py \
  Parte_1_Generador_Caracteres/src/model.py \
  Parte_1_Generador_Caracteres/src/train.py \
  Parte_1_Generador_Caracteres/src/sample.py \
  Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb \
  -x "*.pyc" -x "__pycache__/*" -x "*.DS_Store"

echo ""
echo "✓  Paquete creado: $OUT"
echo ""
echo "Pasos en SageMaker:"
echo "  1. Subir sagemaker_rnn_package.zip al file browser de SageMaker"
echo "  2. Abrir una terminal en SageMaker y ejecutar:"
echo "       cd ~"
echo "       unzip sagemaker_rnn_package.zip -d dino_rnn"
echo "       cd dino_rnn"
echo "       pip install torch pandas mlflow --quiet"
echo "  3. Abrir Parte_1_Generador_Caracteres/notebooks/02_rnn_AlanOsorio.ipynb"
echo "     (el notebook ajusta el cwd automáticamente al buscar CLAUDE.md)"
echo "  4. Ejecutar todas las celdas"
echo "  5. Descargar:"
echo "       Parte_1_Generador_Caracteres/models/rnn_AlanOsorio.pt"
echo "       reports/learning_curves_rnn.png"
echo "       data/generated/names_rnn.csv"
echo "  6. Pegar esos archivos en tu repo local en las mismas rutas"
