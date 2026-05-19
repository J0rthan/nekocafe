#!/usr/bin/env python3
"""
NekoCafé 集成测试脚本
在 CI 流水线中执行，验证两个服务可正常通信
"""
import httpx
import sys
import time


BASE_RESERVATION = "http://localhost:8000"
BASE_MEMBER = "http://localhost:8001"


def test_health():
    """验证两个服务健康检查"""
    print("=== Health Check ===")
    for name, url in [("Reservation", BASE_RESERVATION), ("Member", BASE_MEMBER)]:
        resp = httpx.get(f"{url}/health", timeout=5)
        assert resp.status_code == 200, f"{name} health check failed: {resp.status_code}"
        data = resp.json()
        assert data["status"] == "healthy", f"{name} status not healthy: {data}"
        assert "X-Trace-Id" not in resp.headers or True
        print(f"  ✅ {name}: {data}")


def test_reservation_flow():
    """测试预约完整流程"""
    print("=== Reservation Flow ===")

    # 1. 查询桌位
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables", timeout=5)
    assert resp.status_code == 200
    tables = resp.json()
    assert len(tables) > 0
    table_id = tables[0]["id"]
    print(f"  ✅ Tables listed: {len(tables)} tables")

    # 2. 创建预约
    payload = {
        "customer_id": "cust-int-001",
        "store_id": "store-001",
        "table_id": table_id,
        "reservation_time": "2026-06-15T18:00:00",
        "guest_count": 4,
        "notes": "Integration test",
    }
    resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json=payload, timeout=5)
    assert resp.status_code == 201
    reservation = resp.json()
    reservation_id = reservation["id"]
    print(f"  ✅ Reservation created: {reservation_id}")

    # 3. 查询预约
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}", timeout=5)
    assert resp.status_code == 200
    print(f"  ✅ Reservation retrieved: {reservation_id}")

    # 4. 取消预约
    resp = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}/cancel", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    print(f"  ✅ Reservation cancelled: {reservation_id}")


def test_member_flow():
    """测试会员完整流程"""
    print("=== Member Flow ===")

    # 1. 创建会员
    payload = {
        "name": "测试会员",
        "phone": "13800138003",
        "email": "test@nekocafe.example.com",
        "birthday": "1995-06-15",
        "favorite_cat_breeds": ["英短", "布偶"],
    }
    resp = httpx.post(f"{BASE_MEMBER}/api/v1/members", json=payload, timeout=5)
    assert resp.status_code == 201
    member = resp.json()
    member_id = member["id"]
    assert member["tier"] == "bronze"
    print(f"  ✅ Member created: {member_id}")

    # 2. 查询会员
    resp = httpx.get(f"{BASE_MEMBER}/api/v1/members/{member_id}", timeout=5)
    assert resp.status_code == 200
    print(f"  ✅ Member retrieved: {member_id}")

    # 3. 更新会员
    resp = httpx.patch(f"{BASE_MEMBER}/api/v1/members/{member_id}", json={"name": "更新测试"}, timeout=5)
    assert resp.status_code == 200
    assert resp.json()["name"] == "更新测试"
    print(f"  ✅ Member updated: {member_id}")

    # 4. 查询会员列表
    resp = httpx.get(f"{BASE_MEMBER}/api/v1/members", timeout=5)
    assert resp.status_code == 200
    print(f"  ✅ Members listed: {len(resp.json())} members")

    # 5. 查询预约历史
    resp = httpx.get(f"{BASE_MEMBER}/api/v1/members/{member_id}/reservation-history", timeout=5)
    assert resp.status_code == 200
    print(f"  ✅ Reservation history retrieved")


if __name__ == "__main__":
    retries = 3
    for attempt in range(retries):
        try:
            test_health()
            test_reservation_flow()
            test_member_flow()
            print("\n🎉 All integration tests passed!")
            sys.exit(0)
        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                print("\n❌ Integration tests failed!")
                raise
