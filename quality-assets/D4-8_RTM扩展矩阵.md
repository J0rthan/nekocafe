# D4-8 RTM 扩展矩阵 v2

## 需求可追溯性矩阵 (Requirements Traceability Matrix)

将实验一的需求 ID 扩展到测试用例，覆盖从需求到测试的全链路追溯。

---

## Member Service RTM

| REQ ID | 需求描述 | 来源 | 单元测试 | PBT | 契约测试 | 集成测试 | E2E | 状态 |
|--------|---------|------|---------|-----|---------|---------|-----|------|
| REQ-M-01 | 会员服务健康检查 | Exp1 | UT-M-001 | - | - | INT-02 | - | ✅ |
| REQ-M-02 | 注册新会员 | Exp1 | UT-M-002,003 | - | - | INT-07 | E2E-01:Step1 | ✅ |
| REQ-M-03 | 查询会员详情 | Exp1 | UT-M-004,005 | - | CT-M-01,02 | INT-08 | - | ✅ |
| REQ-M-04 | 更新会员信息 | Exp1 | UT-M-006 | - | - | INT-09 | - | ✅ |
| REQ-M-05 | 查询会员列表(含过滤) | Exp1 | UT-M-007,008,009 | - | CT-M-03,04 | INT-10 | - | ✅ |
| REQ-M-06 | 查询会员预约历史 | Exp1 | UT-M-010 | - | CT-M-05,06 | - | - | ✅ |
| REQ-M-07 | 积分计算规则 | Exp1 | UT-test_domain | PBT-M-01..03 | - | - | - | ✅ |
| REQ-M-08 | 会员等级判定与升级 | Exp1 | UT-test_domain | PBT-M-04..06 | - | - | - | ✅ |
| REQ-M-09 | 敏感数据脱敏 | Exp1 | UT-test_domain | PBT-M-07,08 | - | - | - | ✅ |
| REQ-M-10 | 用户输入验证 | Exp1 | UT-test_domain | PBT-M-09,10 | - | - | - | ✅ |
| REQ-NFR-01 | 结构化日志 | Exp1 | UT-Tracing-01 | - | - | INT-12 | - | ✅ |
| REQ-NFR-02 | 分布式追踪(Trace-ID) | Exp1 | UT-Tracing-01 | - | - | INT-12 | - | ✅ |

---

## Reservation Service RTM

| REQ ID | 需求描述 | 来源 | 单元测试 | PBT | 契约测试 | 集成测试 | E2E | 状态 |
|--------|---------|------|---------|-----|---------|---------|-----|------|
| REQ-R-01 | 查询可用桌位 | Exp1 | UT-R-001..003 | PBT-R-01..03 | CT-R-04..06 | INT-03 | E2E-01:Step2 | ✅ |
| REQ-R-02 | 创建预约 | Exp1 | UT-R-004,005 | PBT-R-04..06 | CT-R-02,03 | INT-04 | E2E-01:Step3 | ✅ |
| REQ-R-03 | 查询预约详情 | Exp1 | UT-R-006,007 | - | - | INT-05 | - | ✅ |
| REQ-R-04 | 取消预约 | Exp1 | UT-R-008,009 | PBT-R-07,08 | - | INT-06 | E2E-01:Step4 | ✅ |
| REQ-R-05 | 查询预约列表(含过滤) | Exp1 | UT-R-010 | - | CT-R-01 | INT-11 | E2E-03 | ✅ |
| REQ-R-06 | 价格计算规则 | Exp1 | UT-test_domain | PBT-R-09..12 | - | - | E2E-02 | ✅ |
| REQ-R-07 | 冲突检测 | Exp1 | UT-test_domain | PBT-R-04..06 | - | - | - | ✅ |
| REQ-R-08 | 时间槽生成 | Exp1 | UT-test_domain | - | - | - | - | ✅ |
| REQ-NFR-03 | 请求追踪 | Exp1 | UT-Tracing-01 | - | - | INT-12 | - | ✅ |

---

## E2E 用户旅程 RTM

| Journey ID | 旅程描述 | 涉及需求 | 步骤数 | 验证点 | 状态 |
|-----------|---------|---------|--------|--------|------|
| E2E-01 | 新用户注册→浏览→预约→取消 | REQ-M-02, REQ-R-01,02,04 | 4 | 全链路通过 | ✅ |
| E2E-02 | 老会员→推荐→下单→支付→评价 | REQ-R-06, REQ-M-06 | 5 | 全链路通过 | ✅ |
| E2E-03 | 店员→接单→调度→完单→看板 | REQ-R-04,05 | 4 | 全链路通过 | ✅ |

---

## 服务间契约 RTM

| Contract ID | 消费者 | 提供者 | 端点 | 需求 |
|------------|--------|--------|------|------|
| CT-M-01 | Reservation | Member | GET /members/{id} | REQ-M-03 |
| CT-M-02 | Reservation | Member | GET /members?tier= | REQ-M-05 |
| CT-M-03 | Reservation | Member | GET /members/{id}/reservation-history | REQ-M-06 |
| CT-R-01 | Member | Reservation | GET /reservations?customer_id= | REQ-R-05 |
| CT-R-02 | Member | Reservation | POST /reservations | REQ-R-02 |
| CT-R-03 | Gateway | Reservation | GET /reservations/tables | REQ-R-01 |

---

## 非功能需求 RTM

| NFR ID | 需求描述 | 测试类型 | 工具 | 结果 |
|--------|---------|---------|------|------|
| NFR-P-01 | P95 < 2s | 性能测试 | k6 | ✅ 120ms |
| NFR-P-02 | 50 VU 无错误 | 压力测试 | k6 | ✅ 0% 错误率 |
| NFR-S-01 | 无高危漏洞 | SAST | Bandit | ✅ 0 HIGH |
| NFR-S-02 | 容器无严重漏洞 | 镜像扫描 | Trivy | ✅ 0 CRITICAL |
| NFR-S-03 | 敏感数据脱敏 | 单元测试 | PBT | ✅ |
| NFR-A-01 | Lighthouse A11y ≥ 90 | 可访问性 | axe-core | ✅ 95分 |
| NFR-Q-01 | 覆盖率 ≥ 70% | 覆盖率 | pytest-cov | ✅ 94%/93% |
| NFR-Q-02 | 变异分数 ≥ 60% | 变异测试 | mutmut | ✅ 66.7% |

---

## 覆盖率统计

| 指标 | 数值 |
|------|------|
| 总需求数 | 22 |
| 总测试用例数 | 133+ |
| 需求覆盖率 | 100% (22/22) |
| 每需求平均测试数 | 6.0 |
| 未覆盖需求 | 0 |
