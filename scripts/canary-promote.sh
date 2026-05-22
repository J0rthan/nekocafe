#!/bin/bash
# ============================================================
# NekoCafé 金丝雀推进脚本
# 用法: bash scripts/canary-promote.sh <env> <weight> [image-org] [image-tag]
# 示例: bash scripts/canary-promote.sh staging 100 j0rthan/nekocafe latest
# ============================================================
set -euo pipefail

ENV="${1:-staging}"
WEIGHT="${2:-100}"
IMAGE_ORG="${3:-nekocafe}"
IMAGE_TAG="${4:-latest}"
NAMESPACE="nekocafe-${ENV}"

echo "🐤 Promoting canary in ${ENV} to ${WEIGHT}%..."

helm upgrade nekocafe-canary infra/helm/nekocafe/ \
  -f "infra/helm/nekocafe/values-${ENV}.yaml" \
  --set canary.enabled="${WEIGHT}" \
  --set canary.weight="${WEIGHT}" \
  --set serviceMonitor.enabled=false \
  --set ingress.enabled=false \
  -n "${NAMESPACE}" \
  --reuse-values \
  --wait \
  --timeout 5m

if [ "${WEIGHT}" -eq 100 ]; then
  echo "🎉 Promoting to stable release..."
  helm upgrade --install nekocafe infra/helm/nekocafe/ \
    -f "infra/helm/nekocafe/values-${ENV}.yaml" \
    --set canary.enabled=false \
    --set canary.weight=0 \
    --set serviceMonitor.enabled=false \
    --set ingress.enabled=false \
    --set global.imageOrg="${IMAGE_ORG}" \
    --set image.tag="${IMAGE_TAG}" \
    -n "${NAMESPACE}" \
    --wait \
    --timeout 5m

  echo "🧹 Cleaning up canary resources..."
  helm uninstall nekocafe-canary -n "${NAMESPACE}" || true
fi

echo "✅ Canary promotion to ${WEIGHT}% complete for ${ENV}."
