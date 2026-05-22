#!/usr/bin/env python3
"""
NekoCafé 集成测试套件 v2 (实验四)
使用 httpx 对运行中的服务进行集成测试 (≥10 个测试)
依赖 Docker Compose 启动的真实数据库和消息队列环境
"""
import httpx
import sys
import time
import json


BASE_RESERVATION = "http://localhost:8000"
BASE_MEMBER = "http://localhost:8001"

passed = 0
failed = 0


def log_result(name: str, success: bool, detail: str = ""):
    global passed, failed
    if success:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


# ============================================================
# Test 1: 健康检查 - Reservation 服务
# ============================================================
def test_int_01_health_reservation():
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/health", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["status"] == "healthy" and data["service"] == "reservation"
        log_result("INT-01: Reservation 健康检查", ok)
        return ok
    except Exception as e:
        log_result("INT-01: Reservation 健康检查", False, str(e))
        return False


# ============================================================
# Test 2: 健康检查 - Member 服务
# ============================================================
def test_int_02_health_member():
    try:
        resp = httpx.get(f"{BASE_MEMBER}/health", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["status"] == "healthy" and data["service"] == "member"
        log_result("INT-02: Member 健康检查", ok)
        return ok
    except Exception as e:
        log_result("INT-02: Member 健康检查", False, str(e))
        return False


# ============================================================
# Test 3: 查询桌位列表（带数据库）
# ============================================================
def test_int_03_list_tables():
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables", timeout=5)
        tables = resp.json()
        ok = resp.status_code == 200 and len(tables) > 0 and "capacity" in tables[0]
        log_result("INT-03: 查询桌位列表", ok)
        return ok, tables[0]["id"] if ok else None
    except Exception as e:
        log_result("INT-03: 查询桌位列表", False, str(e))
        return False, None


# ============================================================
# Test 4: 创建预约（带真实 PostgreSQL）
# ============================================================
def test_int_04_create_reservation(table_id: str):
    try:
        payload = {
            "customer_id": "cust-int-v2-001",
            "store_id": "store-001",
            "table_id": table_id,
            "reservation_time": "2026-08-01T18:30:00",
            "guest_count": 4,
            "notes": "Integration test v2",
        }
        resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json=payload, timeout=5)
        data = resp.json()
        ok = resp.status_code == 201 and data["status"] == "pending" and "id" in data
        log_result("INT-04: 创建预约", ok)
        return ok, data.get("id") if ok else None
    except Exception as e:
        log_result("INT-04: 创建预约", False, str(e))
        return False, None


# ============================================================
# Test 5: 查询预约详情（跨服务数据一致性）
# ============================================================
def test_int_05_get_reservation(reservation_id):
    if not reservation_id:
        log_result("INT-05: 查询预约详情", False, "无有效 reservation_id")
        return False
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["id"] == reservation_id
        log_result("INT-05: 查询预约详情", ok)
        return ok
    except Exception as e:
        log_result("INT-05: 查询预约详情", False, str(e))
        return False


# ============================================================
# Test 6: 取消预约（状态变更）
# ============================================================
def test_int_06_cancel_reservation(reservation_id):
    if not reservation_id:
        log_result("INT-06: 取消预约", False, "无有效 reservation_id")
        return False
    try:
        resp = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}/cancel", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["status"] == "cancelled"
        log_result("INT-06: 取消预约", ok)
        return ok
    except Exception as e:
        log_result("INT-06: 取消预约", False, str(e))
        return False


# ============================================================
# Test 7: 创建会员
# ============================================================
def test_int_07_create_member():
    try:
        payload = {
            "name": "集成测试会员",
            "phone": "13900139003",
            "email": "int-test@nekocafe.example.com",
            "birthday": "1998-08-08",
            "favorite_cat_breeds": ["英短", "暹罗"],
        }
        resp = httpx.post(f"{BASE_MEMBER}/api/v1/members", json=payload, timeout=5)
        data = resp.json()
        ok = resp.status_code == 201 and data["tier"] == "bronze" and data["points"] == 0
        log_result("INT-07: 创建会员", ok)
        return ok, data.get("id") if ok else None
    except Exception as e:
        log_result("INT-07: 创建会员", False, str(e))
        return False, None


# ============================================================
# Test 8: 查询会员详情
# ============================================================
def test_int_08_get_member(member_id):
    if not member_id:
        log_result("INT-08: 查询会员详情", False, "无有效 member_id")
        return False
    try:
        resp = httpx.get(f"{BASE_MEMBER}/api/v1/members/{member_id}", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["id"] == member_id
        log_result("INT-08: 查询会员详情", ok)
        return ok
    except Exception as e:
        log_result("INT-08: 查询会员详情", False, str(e))
        return False


# ============================================================
# Test 9: 更新会员信息
# ============================================================
def test_int_09_update_member(member_id):
    if not member_id:
        log_result("INT-09: 更新会员信息", False, "无有效 member_id")
        return False
    try:
        resp = httpx.patch(f"{BASE_MEMBER}/api/v1/members/{member_id}", json={
            "name": "更新的集成测试会员",
            "email": "updated@nekocafe.example.com",
        }, timeout=5)
        data = resp.json()
        ok = resp.status_code == 200 and data["name"] == "更新的集成测试会员"
        log_result("INT-09: 更新会员信息", ok)
        return ok
    except Exception as e:
        log_result("INT-09: 更新会员信息", False, str(e))
        return False


# ============================================================
# Test 10: 按等级过滤会员
# ============================================================
def test_int_10_filter_members_by_tier():
    try:
        resp = httpx.get(f"{BASE_MEMBER}/api/v1/members?tier=bronze&limit=5", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200
        for m in data:
            if m["tier"] != "bronze":
                ok = False
                break
        log_result("INT-10: 按等级过滤会员", ok)
        return ok
    except Exception as e:
        log_result("INT-10: 按等级过滤会员", False, str(e))
        return False


# ============================================================
# Test 11: 预约列表按客户过滤
# ============================================================
def test_int_11_filter_reservations_by_customer():
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations?customer_id=cust-int-v2-001", timeout=5)
        data = resp.json()
        ok = resp.status_code == 200
        for r in data:
            if r["customer_id"] != "cust-int-v2-001":
                ok = False
                break
        log_result("INT-11: 预约按客户过滤", ok)
        return ok
    except Exception as e:
        log_result("INT-11: 预约按客户过滤", False, str(e))
        return False


# ============================================================
# Test 12: Trace ID 传播（跨服务追踪）
# ============================================================
def test_int_12_trace_id_propagation():
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/health", timeout=5)
        ok = "X-Trace-Id" in resp.headers
        resp2 = httpx.get(f"{BASE_MEMBER}/health", timeout=5)
        ok = ok and "X-Trace-Id" in resp2.headers
        log_result("INT-12: Trace ID 传播", ok)
        return ok
    except Exception as e:
        log_result("INT-12: Trace ID 传播", False, str(e))
        return False


# ============================================================
# Test 13: 重复取消预约（幂等性）
# ============================================================
def test_int_13_double_cancel():
    try:
        # 创建预约
        resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json={
            "customer_id": "cust-double-cancel",
            "store_id": "store-001",
            "table_id": "tbl-003",
            "reservation_time": "2026-09-01T18:00:00",
            "guest_count": 2,
        }, timeout=5)
        assert resp.status_code == 201
        rid = resp.json()["id"]

        # 第一次取消
        r1 = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{rid}/cancel", timeout=5)
        ok = r1.status_code == 200

        # 第二次取消应返回 400
        r2 = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{rid}/cancel", timeout=5)
        ok = ok and r2.status_code == 400
        log_result("INT-13: 重复取消幂等性", ok)
        return ok
    except Exception as e:
        log_result("INT-13: 重复取消幂等性", False, str(e))
        return False


# ============================================================
# Test 14: 创建会员 - 无效手机号
# ============================================================
def test_int_14_invalid_phone_rejected():
    try:
        resp = httpx.post(f"{BASE_MEMBER}/api/v1/members", json={
            "name": "无效手机号",
            "phone": "12345",
        }, timeout=5)
        ok = resp.status_code == 422
        log_result("INT-14: 无效手机号被拒绝", ok)
        return ok
    except Exception as e:
        log_result("INT-14: 无效手机号被拒绝", False, str(e))
        return False


# ============================================================
# Test 15: 查询不存在预约返回 404
# ============================================================
def test_int_15_reservation_not_found():
    try:
        resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/00000000-0000-0000-0000-000000000000", timeout=5)
        ok = resp.status_code == 404
        log_result("INT-15: 不存在预约返回404", ok)
        return ok
    except Exception as e:
        log_result("INT-15: 不存在预约返回404", False, str(e))
        return False


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NekoCafé 集成测试 v2 (实验四)")
    print("=" * 60)

    # 等待服务就绪
    print("\n⏳ 等待服务就绪...")
    for i in range(15):
        try:
            r = httpx.get(f"{BASE_RESERVATION}/health", timeout=3)
            m = httpx.get(f"{BASE_MEMBER}/health", timeout=3)
            if r.status_code == 200 and m.status_code == 200:
                print(f"✅ 第{i+1}秒: 服务就绪")
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        print("❌ 服务启动超时")
        sys.exit(1)

    # Stage 1: 健康检查
    test_int_01_health_reservation()
    test_int_02_health_member()

    # Stage 2: 预约流程
    ok, table_id = test_int_03_list_tables()
    ok2, reservation_id = test_int_04_create_reservation(table_id or "tbl-001")
    test_int_05_get_reservation(reservation_id)
    test_int_06_cancel_reservation(reservation_id)

    # Stage 3: 会员流程
    ok3, member_id = test_int_07_create_member()
    test_int_08_get_member(member_id)
    test_int_09_update_member(member_id)

    # Stage 4: 过滤与查询
    test_int_10_filter_members_by_tier()
    test_int_11_filter_reservations_by_customer()

    # Stage 5: 横切关注点
    test_int_12_trace_id_propagation()
    test_int_13_double_cancel()
    test_int_14_invalid_phone_rejected()
    test_int_15_reservation_not_found()

    # Summary
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"集成测试结果: {passed}/{total} 通过 ({failed} 失败)")
    print(f"{'=' * 60}\n")

    if failed > 0:
        sys.exit(1)
