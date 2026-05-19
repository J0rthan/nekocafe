# NekoCafé 运维手册

## 目录
1. [系统概述](#系统概述)
2. [环境信息](#环境信息)
3. [常见操作](#常见操作)
4. [故障处理](#故障处理)
5. [监控告警](#监控告警)

## 系统概述

NekoCafé 猫咪主题餐饮预约平台基于微服务架构，核心服务包括：
- **Reservation Service** (预约服务): 端口 8000
- **Member Service** (会员服务): 端口 8001

依赖服务: PostgreSQL、Redis、Prometheus、Grafana、Loki、Tempo

## 环境信息

| 环境 | K8s Namespace | 访问入口 |
|------|---------------|----------|
| dev | nekocafe-dev | http://dev.nekocafe.local |
| staging | nekocafe-staging | https://api-staging.nekocafe.example.com |
| prod | nekocafe-prod | https://api.nekocafe.example.com |

## 常见操作

### 部署服务
```bash
# Dev 环境
helm upgrade --install nekocafe infra/helm/nekocafe/ \
  -f infra/helm/nekocafe/values-dev.yaml \
  -n nekocafe-dev --create-namespace

# Staging 环境 (金丝雀 5%)
helm upgrade --install nekocafe-canary infra/helm/nekocafe/ \
  -f infra/helm/nekocafe/values-staging.yaml \
  --set canary.enabled=true --set canary.weight=5 \
  -n nekocafe-staging --create-namespace
```

### 查看服务状态
```bash
kubectl get pods -n nekocafe-prod
kubectl logs -f deployment/nekocafe-reservation -n nekocafe-prod
```

### 回滚
```bash
bash scripts/rollback.sh prod
```

### 扩容
```bash
kubectl scale deployment nekocafe-reservation --replicas=5 -n nekocafe-prod
```

## 故障处理

### 服务宕机 (ServiceDown)
1. 检查 Pod 状态: `kubectl describe pod <pod-name> -n <namespace>`
2. 检查日志: `kubectl logs <pod-name> -n <namespace> --tail=100`
3. 检查资源使用: `kubectl top pod -n <namespace>`
4. 如 HPA 触发: 检查 `kubectl describe hpa -n <namespace>`
5. 如无法快速恢复: 执行 `bash scripts/rollback.sh <env>`

### 高错误率 (HighErrorRate > 1%)
1. 在 Grafana 查看错误分布: NekoCafé Dashboard → Error Rate
2. 在 Tempo 查看慢/失败链路: 按 traceId 搜索
3. 检查数据库连接: `kubectl exec -it deployment/postgresql -- psql -U nekocafe`
4. 如确认代码 Bug: 回滚到上一版本

### 高延迟 (P95 > 500ms)
1. 检查 HPA 是否正常工作: `kubectl describe hpa -n <namespace>`
2. 检查数据库慢查询
3. 检查节点资源
4. 考虑手动扩容或回滚

## 监控告警

### Prometheus 告警规则
- ServiceDown: 服务宕机 > 1min → Critical
- HighErrorRate: 5xx 错误率 > 1% → Critical  
- HighLatency: P95 > 500ms → Warning
- HighMemoryUsage: > 85% → Warning

### Grafana
- URL: http://grafana:3000
- Dashboard: NekoCafé - Service Dashboard
- 数据源: Prometheus + Loki + Tempo

### 日志查询 (Loki)
在 Grafana Explore 中使用 LogQL:
```logql
{service="reservation"} |= "ERROR"
{service="member"} | json | status > 400
```
