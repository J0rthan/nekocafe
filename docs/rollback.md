# NekoCafé 回滚操作手册

## 回滚触发条件

以下任一条件触发自动回滚：
- P95 延迟 > 500ms 持续时间 > 3 分钟
- 5xx 错误率 > 1% 持续时间 > 2 分钟
- 服务 Pod 全部 Unavailable

## 一键回滚

```bash
# 语法
bash scripts/rollback.sh <environment>

# 示例
bash scripts/rollback.sh dev
bash scripts/rollback.sh staging
bash scripts/rollback.sh prod
```

## 手动回滚步骤

### 1. 查看部署历史
```bash
helm history nekocafe -n nekocafe-prod
```

输出示例:
```
REVISION  UPDATED                   STATUS      CHART         DESCRIPTION
1         Mon May 18 10:00:00 2026  superseded  nekocafe-1.0  Install complete
2         Mon May 18 12:00:00 2026  deployed    nekocafe-1.0  Upgrade complete
```

### 2. 回滚到指定版本
```bash
helm rollback nekocafe <revision> -n nekocafe-prod --wait
```

### 3. 验证回滚
```bash
kubectl rollout status deployment/nekocafe-reservation -n nekocafe-prod
kubectl rollout status deployment/nekocafe-member -n nekocafe-prod
curl -s https://api.nekocafe.example.com/health
```

### 4. 通知团队
在团队 Slack/飞书群发布回滚通知：
```
[回滚通知]
环境: prod
原因: HighErrorRate > 1%
回滚至: revision 1 (v1.0.0)
时长: ~2 分钟
状态: 服务已恢复
```

## 金丝雀回滚

如果金丝雀阶段发现问题：

```bash
# 1. 删除金丝雀部署
helm uninstall nekocafe-canary -n nekocafe-prod

# 2. 确保稳定版正常运行
kubectl get pods -n nekocafe-prod -l app=reservation
```

## 数据库回滚

如果部署涉及数据库迁移，需要执行数据库回滚：

```bash
# PostgreSQL 回滚
kubectl exec -it deployment/postgresql -n nekocafe-prod -- \
  psql -U nekocafe -d nekocafe -c "ROLLBACK;"
```

## 回滚后检查清单

- [ ] 所有 Pod Running / Ready
- [ ] Health endpoint 返回 200
- [ ] Grafana 错误率恢复正常
- [ ] Grafana 延迟恢复正常
- [ ] 用户反馈正常
- [ ] 记录 Postmortem 文档
