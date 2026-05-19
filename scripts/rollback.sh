#!/bin/bash
# ============================================================
# NekoCafé 一键回滚脚本
# 用法: bash scripts/rollback.sh <env>
# ============================================================
set -euo pipefail

ENV="${1:-staging}"
NAMESPACE="nekocafe-${ENV}"

echo "🔄 Rolling back deployment in ${ENV} environment..."

# 1. 获取上一个稳定版本
PREVIOUS_REVISION=$(helm history nekocafe -n "${NAMESPACE}" --max 10 | grep "deployed" | tail -2 | head -1 | awk '{print $1}')

if [ -z "${PREVIOUS_REVISION}" ]; then
  echo "❌ No previous stable revision found!"
  exit 1
fi

echo "📦 Rolling back to revision ${PREVIOUS_REVISION}..."

# 2. 执行 Helm 回滚
helm rollback nekocafe "${PREVIOUS_REVISION}" -n "${NAMESPACE}" --wait --timeout 5m

# 3. 验证回滚结果
echo "🔍 Verifying rollback..."
kubectl rollout status deployment/reservation -n "${NAMESPACE}" --timeout=3m
kubectl rollout status deployment/member -n "${NAMESPACE}" --timeout=3m

# 4. 健康检查
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
if curl -sf "${HEALTH_URL}" > /dev/null; then
  echo "✅ Rollback successful! Service is healthy."
else
  echo "⚠️  Rollback completed but health check failed. Manual intervention required."
  exit 1
fi

# 5. 记录回滚事件
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] ROLLBACK: ${ENV} -> revision ${PREVIOUS_REVISION}" >> /tmp/nekocafe-rollback.log
echo "📝 Rollback event logged."
