#!/bin/bash
# ============================================================
# NekoCafé 金丝雀推进脚本
# 用法: bash scripts/canary-promote.sh <env> <weight>
# 示例: bash scripts/canary-promote.sh staging 100
# ============================================================
set -euo pipefail

ENV="${1:-staging}"
WEIGHT="${2:-100}"
NAMESPACE="nekocafe-${ENV}"

echo "🐤 Promoting canary in ${ENV} to ${WEIGHT}%..."

# 逐步推进权重（5% → 25% → 50% → 100%）
# 当前简化为直接设置目标权重
helm upgrade nekocafe-canary infra/helm/nekocafe/ \
  -f "infra/helm/nekocafe/values-${ENV}.yaml" \
  --set canary.enabled="${WEIGHT}" \
  --set canary.weight="${WEIGHT}" \
  -n "${NAMESPACE}" \
  --reuse-values \
  --wait \
  --timeout 5m

# 当推进到 100% 时，清理金丝雀资源并切换稳定版
if [ "${WEIGHT}" -eq 100 ]; then
  echo "🎉 Promoting to stable release..."
  helm upgrade --install nekocafe infra/helm/nekocafe/ \
    -f "infra/helm/nekocafe/values-${ENV}.yaml" \
    --set canary.enabled=false \
    --set canary.weight=0 \
    -n "${NAMESPACE}" \
    --wait \
    --timeout 5m

  echo "🧹 Cleaning up canary resources..."
  helm uninstall nekocafe-canary -n "${NAMESPACE}" || true
fi

echo "✅ Canary promotion to ${WEIGHT}% complete for ${ENV}."
