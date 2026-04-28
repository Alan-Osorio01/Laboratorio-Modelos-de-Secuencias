#!/usr/bin/env bash
# Sube el frontend estático a S3 e invalida CloudFront.
#
# Variables esperadas (export antes o pasar en el comando):
#   S3_BUCKET                — nombre del bucket S3 que aloja el sitio
#   CLOUDFRONT_DISTRIBUTION  — id de la distribución (vacío para saltar invalidación)
#   AWS_REGION               — región AWS (default: us-east-1)
#
# Uso:
#   S3_BUCKET=dino-lab-frontend bash Parte_4_Integracion_Web/web/deploy_s3.sh

set -euo pipefail

: "${S3_BUCKET:?Define S3_BUCKET (export S3_BUCKET=...)}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLOUDFRONT_DISTRIBUTION="${CLOUDFRONT_DISTRIBUTION:-}"

WEB_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "→ sincronizando $WEB_DIR  →  s3://${S3_BUCKET}/"

aws s3 sync "$WEB_DIR" "s3://${S3_BUCKET}/" \
  --region "$AWS_REGION" \
  --delete \
  --exclude "deploy_s3.sh" \
  --exclude "*.sh" \
  --cache-control "public, max-age=300"

if [[ -n "$CLOUDFRONT_DISTRIBUTION" ]]; then
  echo "→ invalidando CloudFront ($CLOUDFRONT_DISTRIBUTION)"
  aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION" \
    --paths "/*" >/dev/null
fi

echo "✓ deploy completo"
echo "  bucket:       s3://${S3_BUCKET}/"
echo "  endpoint S3:  http://${S3_BUCKET}.s3-website-${AWS_REGION}.amazonaws.com/"
[[ -n "$CLOUDFRONT_DISTRIBUTION" ]] && echo "  cloudfront:   distribución $CLOUDFRONT_DISTRIBUTION invalidada"
