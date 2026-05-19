#!/usr/bin/env python3
"""
生成 D3-4 CICD配置与运行截图.docx
"""
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)

doc.add_paragraph()
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('NekoCafé CI/CD 配置与运行截图')
run.bold = True
run.font.size = Pt(22)
run.font.name = '黑体'

doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info.add_run('D3-4\n').font.size = Pt(14)
info.add_run('《软件工程》实验三 · DevOps 流水线与容器化部署\n').font.size = Pt(12)
info.add_run('版本：v1.0 · 2026-05').font.size = Pt(11)

doc.add_page_break()

# ==== 1. CI 流水线 ====
doc.add_heading('1 CI 流水线 (ci.yml)', level=1)

doc.add_heading('1.1 流水线概览', level=2)
doc.add_paragraph(
    'CI 流水线文件路径：.github/workflows/ci.yml\n'
    '触发条件：\n'
    '• pull_request: 目标分支 main / develop\n'
    '• push: main 分支\n'
    '路径过滤：services/**, .github/workflows/ci.yml\n\n'
    '流水线阶段：\n'
    '1. Lint Check — flake8 + black + hadolint (约 1 分钟)\n'
    '2. Unit Tests — pytest + coverage（约 2 分钟）\n'
    '3. SAST Scan — Bandit 安全扫描（约 30 秒）\n'
    '4. Build Images — Docker 多阶段构建（约 2 分钟）\n'
    '5. Container Scan — Trivy 漏洞扫描（约 1 分钟）\n'
    '6. Integration Test — Docker Compose 起栈测试（约 2 分钟）\n'
    '7. Push Image — 推送 GHCR（约 1 分钟）\n'
    '8. PR Comment — 自动评论汇总（约 10 秒）\n\n'
    '预估总时长：约 8-10 分钟（含缓存），满足 ≤ 10 分钟要求。'
)

doc.add_heading('1.2 YAML 关键配置说明', level=2)

doc.add_heading('缓存策略', level=3)
doc.add_paragraph(
    '1. pip 缓存：actions/setup-python 的 cache: pip\n'
    '2. Docker Layer 缓存：\n'
    '   cache-from: type=gha\n'
    '   cache-to: type=gha,mode=max\n'
    '   利用 GitHub Actions Cache API 缓存 Docker 层\n'
    '3. Job Artifact 传递：\n'
    '   Coverage XML 通过 actions/upload-artifact 传递到 PR Comment 阶段'
)

doc.add_heading('并行策略', level=3)
doc.add_paragraph(
    '• Unit Test: matrix 策略，reservation 和 member 并行运行\n'
    '• Build: matrix 策略，两个服务并行构建镜像\n'
    '• Container Scan: matrix 策略，并行扫描\n'
    '• 有依赖关系的 Stage 串行执行（如 Integration Test 依赖 Build 完成）'
)

doc.add_heading('1.3 CI 关键阶段 YAML 摘录', level=2)

ci_yaml_excerpt = '''# Stage 2: Unit Test
unit-test:
  needs: lint
  strategy:
    matrix:
      service: [reservation, member]
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    - run: |
        cd services/${{ matrix.service }}
        pytest tests/ --cov=src --cov-report=xml

# Stage 5: Container Scan (Trivy)
container-scan:
  needs: build
  steps:
    - uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:ci-${{ github.sha }}
        format: 'sarif'
        severity: 'HIGH,CRITICAL'
        exit-code: '0\''''
doc.add_paragraph(ci_yaml_excerpt)

# ==== 2. CD 流水线 ====
doc.add_heading('2 CD 流水线 (cd.yml)', level=1)

doc.add_heading('2.1 流水线概览', level=2)
doc.add_paragraph(
    'CD 流水线路径：.github/workflows/cd.yml\n'
    '触发条件：\n'
    '• push: main 分支（自动部署 dev）\n'
    '• workflow_dispatch: 手动选择环境和策略\n\n'
    '部署阶段：\n'
    '1. deploy-dev — 自动部署（合并 main 触发或手动）\n'
    '2. deploy-staging — 金丝雀 5%，监控 5 分钟\n'
    '3. deploy-prod — 金丝雀 5%，监控 10 分钟，手动审批\n'
    '4. auto-rollback — 失败自动回滚'
)

doc.add_heading('2.2 Environment Protection', level=2)
doc.add_paragraph(
    'GitHub Environment 配置：\n\n'
    '• dev — 无保护，自动部署\n'
    '• staging — 无保护，自动部署\n'
    '• production — 需要审批者 (Required Reviewer)，手动批准后才能部署\n\n'
    '每个 Environment 配置独立的：\n'
    '• KUBECONFIG Secret（Base64 编码的 kubeconfig）\n'
    '• 环境特定的 URL'
)

doc.add_heading('2.3 金丝雀部署 YAML 摘录', level=2)
canary_excerpt = '''deploy-staging:
  environment: staging
  steps:
    - name: Deploy Canary 5%
      run: |
        helm upgrade --install nekocafe-canary infra/helm/nekocafe/ \\
          -f infra/helm/nekocafe/values-staging.yaml \\
          --set canary.enabled=true \\
          --set canary.weight=5 \\
          -n nekocafe-staging --create-namespace

    - name: Monitor canary health (5 min)
      run: |
        for i in $(seq 1 10); do
          sleep 30
          ERROR_RATE=$(curl -s prometheus:9090/api/v1/query?query=...)
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            bash scripts/rollback.sh staging
            exit 1
          fi
        done

    - name: Promote to 100%
      run: bash scripts/canary-promote.sh staging 100'''
doc.add_paragraph(canary_excerpt)

# ==== 3. 缓存与并发优化 ====
doc.add_heading('3 缓存与并发优化', level=1)

doc.add_paragraph(
    '1. GitHub Actions Cache：\n'
    '   • pip cache: setup-python 内置支持\n'
    '   • Docker cache: gha 类型缓存，跨 workflow run 复用\n\n'
    '2. Job Matrix 并发：\n'
    '   • Unit Test / Build / Scan 均使用 matrix 并行\n'
    '   • 两个服务同时运行，节省 ~50% 时间\n\n'
    '3. 路径过滤：\n'
    '   • paths 配置确保仅服务代码变更才触发流水线\n'
    '   • README/docs 变更不触发 CI\n\n'
    '4. 失败快速中断：\n'
    '   • needs 依赖配置保证阶段失败立即中断后续\n'
    '   • 避免浪费资源和等待时间'
)

# ==== 4. 常见失败与处置手册 ====
doc.add_heading('4 常见失败与处置手册', level=1)

failures = [
    ('Lint 失败',
     '运行 make format 自动格式化；检查 flake8 错误信息修正'),
    ('Unit Test 失败',
     '查看 pytest 输出的具体测试用例；本地复现：make test'),
    ('SAST 高危告警',
     '查看 bandit-report.json；评估是否为误报（False Positive）；'
     '确认修复后重新提交'),
    ('Docker Build 失败',
     '检查 Dockerfile 语法；确保 COPY 路径正确；检查 .dockerignore'),
    ('Trivy HIGH/CRITICAL 漏洞',
     '检查 CVE 详情；尝试升级依赖版本；如无可用修复则评估实际风险'),
    ('Integration Test 失败',
     '本地 docker compose up 复现；检查健康检查端点；查看 Docker 日志'),
    ('镜像推送失败',
     '检查 GHCR 登录状态；确认 GitHub Token 权限包含 write:packages'),
    ('Helm 部署失败',
     '运行 helm lint 检查语法；kubectl describe pod 查看 Pod 事件'),
]

table = doc.add_table(rows=len(failures) + 1, cols=2)
table.style = 'Light Grid Accent 1'
table.rows[0].cells[0].text = '失败类型'
table.rows[0].cells[1].text = '处置方法'
for i, (failure, fix) in enumerate(failures):
    table.rows[i + 1].cells[0].text = failure
    table.rows[i + 1].cells[1].text = fix

doc.add_page_break()
doc.add_paragraph()
disclaimer = doc.add_paragraph()
disclaimer.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = disclaimer.add_run(
    '本人承诺所提交的实验材料系本人（团队）独立完成，对引用的他人成果均已明确标注。'
    'AI 生成内容已在附录中说明使用范围与提示词，并对其正确性负责。'
)
run.font.size = Pt(10)
run.italic = True

output_path = os.path.join(BASE_DIR, '..', '..', 'D3-4_CICD配置与运行截图.docx')
doc.save(output_path)
print(f'✅ D3-4 generated: {output_path}')
