VENV := venv
VENV_PIP := $(VENV)/bin/pip
VENV_PYTEST := $(VENV)/bin/pytest
VENV_FLAKE8 := $(VENV)/bin/flake8
VENV_BLACK := $(VENV)/bin/black
VENV_BANDIT := $(VENV)/bin/bandit

.PHONY: help venv up down build test lint scan clean dev-deps

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## 创建虚拟环境
	python3 -m venv $(VENV)
	@echo "✅ 虚拟环境已创建: $(VENV)"

dev-deps: venv ## 安装开发依赖
	$(VENV_PIP) install -r services/reservation/requirements.txt
	$(VENV_PIP) install -r services/member/requirements.txt
	$(VENV_PIP) install pytest pytest-cov bandit black flake8 pre-commit

up: ## 启动全部服务 (Docker Compose)
	docker compose up -d --build
	@echo "✅ 服务已启动: http://localhost:8000 (预约) http://localhost:8001 (会员)"

down: ## 停止全部服务
	docker compose down -v

build: ## 构建所有服务镜像
	docker build -t ghcr.io/nekocafe/reservation:latest services/reservation/
	docker build -t ghcr.io/nekocafe/member:latest services/member/

test: dev-deps ## 运行所有测试并生成覆盖率报告
	cd services/reservation && $(abspath $(VENV_PYTEST)) tests/ -v --cov=src --cov-report=term-missing --cov-report=xml
	cd services/member && $(abspath $(VENV_PYTEST)) tests/ -v --cov=src --cov-report=term-missing --cov-report=xml

lint: dev-deps ## 代码检查 (flake8 + black)
	$(VENV_FLAKE8) services/ --max-line-length=120 --exclude=__pycache__,venv
	$(VENV_BLACK) --check services/

format: dev-deps ## 自动格式化代码
	$(VENV_BLACK) services/

scan: dev-deps ## 安全扫描 (Bandit SAST)
	$(VENV_BANDIT) -r services/ -f json -o bandit-report.json
	@echo "SAST 扫描完成，报告: bandit-report.json"

image-scan: export TRIVY_DB_REPOSITORY := ghcr.io/aquasecurity/trivy-db
image-scan: export TRIVY_JAVA_DB_REPOSITORY := ghcr.io/aquasecurity/trivy-java-db
image-scan: ## 容器镜像安全扫描 (Trivy)
	trivy image ghcr.io/nekocafe/reservation:latest --severity HIGH,CRITICAL --timeout 20m
	trivy image ghcr.io/nekocafe/member:latest --severity HIGH,CRITICAL --timeout 20m

helm-lint: ## Helm Chart 语法检查
	helm lint infra/helm/nekocafe/
	helm template test infra/helm/nekocafe/ -f infra/helm/nekocafe/values-dev.yaml > /dev/null

k8s-lint: ## K8s 清单检查
	kube-linter lint infra/helm/nekocafe/templates/

clean: ## 清理构建产物
	docker compose down -v --rmi all
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '.coverage' -delete
	find . -type f -name 'coverage.xml' -delete
	find . -type f -name 'bandit-report.json' -delete
