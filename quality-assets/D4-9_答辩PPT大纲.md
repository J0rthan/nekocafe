# D4-9 答辩 PPT 大纲 (≤ 15 页)

---

## Slide 1: 封面
- **标题**: NekoCafé 软件质量工程与 AI 辅助代码审查
- **副标题**: 实验四 — 质量保障体系构建
- **团队**: [姓名]
- **日期**: 2026-05-22

---

## Slide 2: 项目背景
- NekoCafé 猫咪主题餐饮预约平台
- 实验三已建立 CI/CD 流水线
- 本次任务: 建立完整的质量保障体系

---

## Slide 3: 质量目标
- **ISO/IEC 25010 八大特性**
- 覆盖率 ≥ 70%, 变异分数 ≥ 60%
- 0 高危漏洞, P95 < 2s
- Lighthouse A11y ≥ 90

---

## Slide 4: 测试金字塔与策略
- 金字塔图: Unit → PBT → Contract → Integration → E2E
- 各层数量预算 (30+/10/6/15/3)
- 测试数据管理策略

---

## Slide 5: 单元测试与 PBT
- Member: 64 tests, 94% coverage
- Reservation: 69 tests, 93% coverage
- 10 组 PBT (hypothesis)
- 5+ 核心域类属性验证

---

## Slide 6: 契约测试
- 6 对消费者-提供者契约
- Member ↔ Reservation 双向契约
- 响应结构、错误处理、过滤参数验证

---

## Slide 7: 集成测试与 E2E
- 15 个集成测试 (Docker Compose)
- 3 条核心用户旅程
- CI 流水线集成

---

## Slide 8: 变异测试
- 变异分数: 66.7%
- 15 个变异体，10 个被杀死
- 边界值/算术/常量/逻辑变异算子

---

## Slide 9: 性能测试
- k6 压测预约接口
- 50 VU 峰值测试
- RT: 45ms avg, 120ms P95
- 错误率: 0%

---

## Slide 10: 安全测试
- Bandit SAST: 0 HIGH
- Trivy 镜像扫描: 0 CRITICAL
- OWASP ZAP Baseline: 0 关键漏洞
- 敏感数据脱敏策略

---

## Slide 11: AI 代码审查
- 3 轮渐进式 AI 审查
- 22 条意见，86.4% 采纳率
- 误报率 13.6%
- AI 优势与局限分析

---

## Slide 12: 缺陷管理
- 14 个缺陷 (GitHub Issues)
- 缺陷四象限分类
- Bug Bash: 5 项流程改进
- 缺陷逃逸率: 0%

---

## Slide 13: 质量度量看板
- 代码覆盖率趋势
- 缺陷热力图
- CI/CD 质量门禁
- 综合评分: 9/10 达标

---

## Slide 14: RTM 可追溯性
- 22 需求 → 133+ 测试用例
- 100% 需求覆盖率
- 端到端追溯链路

---

## Slide 15: 总结与展望
- **成就**: 9/10 质量指标达标
- **增分项**: Semgrep 规则定义、故障注入计划
- **下一步**: v1.1 认证机制、PostgreSQL 迁移
- **心得**: AI 审查 + 传统测试 = 最优质量策略
