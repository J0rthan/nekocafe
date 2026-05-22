// ============================================================
// NekoCafé 性能测试脚本 (k6)
// 压测「桌位预约」接口
// ============================================================

import http from 'k6/http';
import { check, sleep, group, trend } from 'k6';
import { Rate, Counter } from 'k6/metrics';

// 自定义指标
const errorRate = new Rate('errors');
const reservationCounter = new Counter('reservations_created');
const tableQueryTrend = new trend('table_query_duration');
const reservationCreateTrend = new trend('reservation_create_duration');

// 测试配置
export const options = {
  stages: [
    { duration: '30s', target: 5 },   // 预热: 30秒内升至5 VU
    { duration: '1m', target: 20 },    // 加压: 1分钟内升至20 VU
    { duration: '2m', target: 20 },    // 稳态: 保持20 VU 2分钟
    { duration: '30s', target: 50 },   // 峰值: 30秒内升至50 VU
    { duration: '1m', target: 50 },    // 峰值稳态: 保持50 VU 1分钟
    { duration: '30s', target: 0 },    // 冷却: 逐步降至0
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95%请求在2秒内完成
    errors: ['rate<0.05'],             // 错误率低于5%
    http_req_failed: ['rate<0.05'],    // HTTP失败率低于5%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const RESERVATION_API = `${BASE_URL}/api/v1/reservations`;

// 生成随机预约数据
function generateReservationPayload() {
  const storeIds = ['store-001', 'store-002', 'store-003'];
  const tableIds = ['tbl-001', 'tbl-002', 'tbl-003', 'tbl-004', 'tbl-005'];
  const times = ['18:00:00', '18:30:00', '19:00:00', '19:30:00', '20:00:00'];
  const dates = ['2026-07-01', '2026-07-02', '2026-07-03', '2026-07-04', '2026-07-05'];

  return JSON.stringify({
    customer_id: `cust-perf-${Math.floor(Math.random() * 10000)}`,
    store_id: storeIds[Math.floor(Math.random() * storeIds.length)],
    table_id: tableIds[Math.floor(Math.random() * tableIds.length)],
    reservation_time: `${dates[Math.floor(Math.random() * dates.length)]}T${times[Math.floor(Math.random() * times.length)]}`,
    guest_count: Math.floor(Math.random() * 6) + 1,
    notes: 'Performance test',
  });
}

export default function () {
  // ============================================================
  // Scenario 1: 查询桌位 (GET /tables) — 高频读操作
  // ============================================================
  group('GET /api/v1/reservations/tables', () => {
    const start = Date.now();
    const res = http.get(`${RESERVATION_API}/tables`, {
      headers: { 'Accept': 'application/json' },
      tags: { name: 'list_tables' },
    });
    tableQueryTrend.add(Date.now() - start);

    const success = check(res, {
      'tables: status 200': (r) => r.status === 200,
      'tables: response is array': (r) => {
        try {
          return Array.isArray(JSON.parse(r.body));
        } catch { return false; }
      },
      'tables: response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    errorRate.add(!success);
  });

  sleep(0.5);

  // ============================================================
  // Scenario 2: 查询预约列表 (GET /reservations) — 读操作
  // ============================================================
  group('GET /api/v1/reservations', () => {
    const start = Date.now();
    const res = http.get(`${RESERVATION_API}?limit=20`, {
      headers: { 'Accept': 'application/json' },
      tags: { name: 'list_reservations' },
    });

    check(res, {
      'list: status 200': (r) => r.status === 200,
      'list: response time < 800ms': (r) => r.timings.duration < 800,
    });
  });

  sleep(0.5);

  // ============================================================
  // Scenario 3: 创建预约 (POST /reservations) — 写操作
  // ============================================================
  group('POST /api/v1/reservations', () => {
    const payload = generateReservationPayload();
    const start = Date.now();
    const res = http.post(RESERVATION_API, payload, {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'create_reservation' },
    });
    reservationCreateTrend.add(Date.now() - start);

    const success = check(res, {
      'create: status 201': (r) => r.status === 201,
      'create: has id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.id && body.status === 'pending';
        } catch { return false; }
      },
      'create: response time < 1500ms': (r) => r.timings.duration < 1500,
    });
    errorRate.add(!success);
    if (success) reservationCounter.add(1);
  });

  sleep(1);
}

// ============================================================
// 测试结束汇总
// ============================================================
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_duration_seconds: data.state.testRunDurationMs / 1000,
    total_requests: data.metrics.http_reqs?.values?.count || 0,
    total_failed: data.metrics.http_req_failed?.values?.fails || 0,
    error_rate: data.metrics.errors?.values?.rate || 0,
    reservations_created: data.metrics.reservations_created?.values?.count || 0,

    response_times_ms: {
      avg: data.metrics.http_req_duration?.values?.avg?.toFixed(2),
      p50: data.metrics.http_req_duration?.values?.p(50)?.toFixed(2),
      p95: data.metrics.http_req_duration?.values?.p(95)?.toFixed(2),
      p99: data.metrics.http_req_duration?.values?.p(99)?.toFixed(2),
      max: data.metrics.http_req_duration?.values?.max?.toFixed(2),
    },

    table_query_avg_ms: data.metrics.table_query_duration?.values?.avg?.toFixed(2),
    reservation_create_avg_ms: data.metrics.reservation_create_duration?.values?.avg?.toFixed(2),
  };

  return {
    'stdout': JSON.stringify(summary, null, 2),
    'quality-assets/reports/k6-summary.json': JSON.stringify(summary, null, 2),
  };
}
