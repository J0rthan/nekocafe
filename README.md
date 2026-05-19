# NekoCafé - 猫咪主题餐饮预约平台 (DevOps Pipeline)

## 项目概述

NekoCafé 是一个面向年轻用户的连锁猫咪主题餐厅预约平台。本仓库实现端到端 DevOps 流水线，覆盖 CI/CD、容器化部署、可观测性与渐进式发布。

## 架构决策：Monorepo vs Polyrepo

**选择：Monorepo**

| 维度 | Monorepo | Polyrepo |
|------|----------|----------|
| 代码共享 | 直接引用，零成本 | 需发布 Package |
| 原子化 Commit | 跨服务一次提交 | 需跨仓库协调 |
| CI/CD 复杂度 | 需路径过滤 | 独立流水线 |
| 团队规模适配 | <20 人最佳 | 适合大团队 |

本项目为 PoC 阶段（2 个服务，<5 人团队），选用 Monorepo 降低协作成本。随服务增长可通过 CI 路径过滤 (`paths-filter`) 实现差异化构建。

## 技术栈

| 类别 | 选型 |
|------|------|
| 运行时 | Python 3.11 + FastAPI |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 容器化 | Docker + Docker Compose |
| 编排 | Kubernetes (Minikube/Kind) + Helm 3 |
| CI/CD | GitHub Actions |
| 镜像仓库 | GitHub Container Registry |
| 可观测性 | OpenTelemetry + Prometheus + Grafana + Loki + Tempo |
| 安全扫描 | Trivy + Bandit |
| 渐进发布 | Canary (Istio/Argo Rollouts) |

## 一键启动（本地）

### 前置要求

- Docker Desktop 24+
- Python 3.11+
- Make

### 快速开始

```bash
# 1. 克隆仓库
git clone <repo-url> && cd nekocafe

# 2. 一键起栈（30 分钟内可完成）
make up

# 3. 验证服务
curl http://localhost:8000/health          # 预约服务
curl http://localhost:8001/health          # 会员服务
curl http://localhost:3000                 # Grafana
```

### 常用命令

```bash
make up          # 启动全部服务
make down        # 停止全部服务
make build       # 构建所有镜像
make test        # 运行所有测试
make lint        # 代码检查
make scan        # 安全扫描
make clean       # 清理资源
```

## 项目结构

```
nekocafe/
├── README.md
├── docker-compose.yml          # 本地一键起栈
├── Makefile                    # 常用命令入口
├── .editorconfig               # 编辑器统一配置
├── .pre-commit-config.yaml     # Pre-commit 钩子
├── services/
│   ├── reservation/            # 预约服务
│   │   ├── src/                # 源代码
│   │   ├── tests/              # 单元测试
│   │   ├── Dockerfile          # 多阶段构建
│   │   └── requirements.txt
│   └── member/                 # 会员服务
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
├── infra/
│   ├── helm/nekocafe/          # Helm Chart
│   │   ├── Chart.yaml
│   │   ├── values.yaml         # 默认值
│   │   ├── values-dev.yaml     # 开发环境
│   │   ├── values-staging.yaml # 预发布环境
│   │   ├── values-prod.yaml    # 生产环境
│   │   └── templates/          # K8s 模板
│   └── observability/          # 可观测性配置
│       ├── grafana/dashboards/
│       ├── prometheus/rules.yml
│       └── loki/config.yml
├── .github/workflows/
│   ├── ci.yml                  # CI 流水线
│   └── cd.yml                  # CD 流水线
├── scripts/
│   ├── rollback.sh             # 一键回滚
│   └── canary-promote.sh       # 金丝雀推进
└── docs/
    ├── runbook.md              # 运维手册
    └── rollback.md             # 回滚操作手册
```

## 环境拓扑

| 环境 | 用途 | 触发方式 | 审批 |
|------|------|----------|------|
| dev | 开发自测 | PR 自动部署 | 无 |
| staging | 预发布验证 | 合并到 main 自动 | 无 |
| prod | 生产环境 | 手动审批 + Canary | 需要 |

## DORA 指标

本项目的 DORA 指标数据见 `D3-7_DORA指标报告.xlsx`。

## 团队

- 北京林业大学 · 信息学院 · 软件工程课程
- 实验三：DevOps 流水线与容器化部署
# nekocafe
# nekocafe
