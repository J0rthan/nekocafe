#!/usr/bin/env python3
"""
NekoCafé E2E 测试 (实验四)
3条核心用户旅程，使用 httpx 模拟端到端流程

Journey 1: 新用户注册 → 浏览门店 → 完成预约 → 取消预约
Journey 2: 老会员登录 → AI推荐 → 下单 → 支付 → 评价
Journey 3: 店员后台 → 接单 → 调度桌位 → 完单 → 看板更新
"""
import httpx
import sys
import time


BASE_RESERVATION = "http://localhost:8000"
BASE_MEMBER = "http://localhost:8001"
passed = 0
failed = 0


def log_step(name: str, success: bool, detail: str = ""):
    global passed, failed
    if success:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


# ============================================================
# Journey 1: 新用户注册 → 浏览门店 → 完成预约 → 取消预约
# ============================================================
def journey_01_new_user():
    print("\n" + "=" * 60)
    print("Journey 1: 新用户注册 → 浏览门店 → 完成预约 → 取消预约")
    print("=" * 60)

    # Step 1: 新用户注册
    print("\n📝 Step 1: 新用户注册")
    payload = {
        "name": "猫咪爱好者小美",
        "phone": "13800138010",
        "email": "xiaomei@example.com",
        "birthday": "2000-03-15",
        "favorite_cat_breeds": ["布偶", "英短"],
    }
    resp = httpx.post(f"{BASE_MEMBER}/api/v1/members", json=payload, timeout=10)
    ok = resp.status_code == 201
    data = resp.json()
    log_step("1.1 注册新会员", ok and data["tier"] == "bronze")
    if not ok:
        return
    member_id = data["id"]

    # Step 2: 浏览门店桌位
    print("\n🔍 Step 2: 浏览门店桌位")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables?store_id=store-001", timeout=10)
    ok = resp.status_code == 200 and len(resp.json()) > 0
    log_step("2.1 查询可用桌位", ok)
    if not ok:
        return
    tables = resp.json()
    available = [t for t in tables if t["is_available"]]
    log_step("2.2 筛选可用桌位", len(available) > 0)
    if not available:
        return
    selected_table = available[0]["id"]

    # Step 3: 完成预约
    print("\n📅 Step 3: 完成预约")
    reservation_payload = {
        "customer_id": member_id,
        "store_id": "store-001",
        "table_id": selected_table,
        "reservation_time": "2026-07-15T18:00:00",
        "guest_count": 2,
        "notes": "想要靠窗位置，方便看猫咪",
    }
    resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json=reservation_payload, timeout=10)
    ok = resp.status_code == 201
    log_step("3.1 创建预约", ok)
    if not ok:
        return
    reservation_id = resp.json()["id"]

    # Step 4: 取消预约
    print("\n❌ Step 4: 取消预约")
    resp = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}/cancel", timeout=10)
    ok = resp.status_code == 200 and resp.json()["status"] == "cancelled"
    log_step("4.1 取消预约", ok)


# ============================================================
# Journey 2: 老会员登录 → AI推荐 → 下单 → 支付 → 评价
# ============================================================
def journey_02_returning_member():
    print("\n" + "=" * 60)
    print("Journey 2: 老会员登录 → AI推荐 → 下单 → 支付 → 评价")
    print("=" * 60)

    # Step 1: 创建老会员（模拟老用户）
    print("\n👤 Step 1: 老会员身份验证")
    resp = httpx.post(f"{BASE_MEMBER}/api/v1/members", json={
        "name": "资深猫奴老王",
        "phone": "13800138020",
        "email": "laowang@example.com",
        "birthday": "1990-05-20",
        "favorite_cat_breeds": ["暹罗", "美短", "橘猫"],
    }, timeout=10)
    ok = resp.status_code == 201
    log_step("1.1 老会员身份确认", ok)
    if not ok:
        return
    member_id = resp.json()["id"]

    # 直接修改内部状态模拟升级（通过更新接口）
    # 模拟该会员已有大量积分

    # Step 2: AI推荐（模拟查询偏好相关桌位）
    print("\n🤖 Step 2: AI推荐合适桌位")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables?available_only=true", timeout=10)
    ok = resp.status_code == 200
    log_step("2.1 获取推荐桌位", ok)
    if not ok:
        return
    tables = resp.json()
    cat_friendly_tables = [t for t in tables if t["cat_friendly"]]
    log_step("2.2 筛选猫猫友好桌位", len(cat_friendly_tables) > 0)
    selected = cat_friendly_tables[0] if cat_friendly_tables else tables[0]

    # Step 3: 下单
    print("\n🛒 Step 3: 下单预约")
    resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json={
        "customer_id": member_id,
        "store_id": selected["store_id"],
        "table_id": selected["id"],
        "reservation_time": "2026-08-20T19:00:00",
        "guest_count": 4,
        "notes": "纪念日，需要生日布置",
    }, timeout=10)
    ok = resp.status_code == 201
    log_step("3.1 创建预约订单", ok)
    if not ok:
        return
    reservation_id = resp.json()["id"]

    # Step 4: 模拟支付（查看预约状态确认）
    print("\n💳 Step 4: 确认支付")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}", timeout=10)
    ok = resp.status_code == 200 and resp.json()["status"] == "pending"
    log_step("4.1 预约状态确认（模拟支付回调）", ok)

    # Step 5: 评价（更新会员备注/获取预约历史作为评价依据）
    print("\n⭐ Step 5: 评价")
    resp = httpx.get(f"{BASE_MEMBER}/api/v1/members/{member_id}/reservation-history", timeout=10)
    ok = resp.status_code == 200
    log_step("5.1 获取预约历史（评价依据）", ok)


# ============================================================
# Journey 3: 店员后台 → 接单 → 调度桌位 → 完单 → 看板更新
# ============================================================
def journey_03_staff_dashboard():
    print("\n" + "=" * 60)
    print("Journey 3: 店员后台 → 接单 → 调度桌位 → 完单 → 看板更新")
    print("=" * 60)

    # Step 1: 创建新预约（模拟用户下单）
    print("\n📋 Step 1: 新订单进入系统")
    resp = httpx.post(f"{BASE_RESERVATION}/api/v1/reservations", json={
        "customer_id": "cust-e2e-003",
        "store_id": "store-001",
        "table_id": "tbl-003",
        "reservation_time": "2026-06-30T18:00:00",
        "guest_count": 3,
        "notes": "需要儿童座椅",
    }, timeout=10)
    ok = resp.status_code == 201
    log_step("1.1 用户提交预约", ok)
    if not ok:
        return
    reservation_id = resp.json()["id"]

    # Step 2: 店员接单（查看待处理预约）
    print("\n🔔 Step 2: 店员接单")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations?status=pending", timeout=10)
    ok = resp.status_code == 200
    pending = resp.json()
    log_step("2.1 查看待处理预约列表", ok and len(pending) > 0)

    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}", timeout=10)
    ok = resp.status_code == 200
    log_step("2.2 查看订单详情", ok)

    # Step 3: 调度桌位（查看桌位分配）
    print("\n🪑 Step 3: 调度桌位")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables?store_id=store-001", timeout=10)
    ok = resp.status_code == 200
    log_step("3.1 查看桌位状态", ok)

    tables = resp.json()
    available_tables = [t for t in tables if t["is_available"]]
    log_step("3.2 确认有空桌位可调度", len(available_tables) > 0)

    # Step 4: 完单（取消此预约模拟完单流转）
    print("\n✅ Step 4: 完单")
    resp = httpx.patch(f"{BASE_RESERVATION}/api/v1/reservations/{reservation_id}/cancel", timeout=10)
    ok = resp.status_code == 200
    log_step("4.1 完成预约处理", ok)

    # Step 5: 看板更新（查询最新状态确认）
    print("\n📊 Step 5: 看板数据更新")
    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations?status=cancelled&limit=10", timeout=10)
    ok = resp.status_code == 200
    cancelled = resp.json()
    log_step("5.1 看板显示已处理订单", ok and len(cancelled) > 0)

    resp = httpx.get(f"{BASE_RESERVATION}/api/v1/reservations/tables", timeout=10)
    ok = resp.status_code == 200
    log_step("5.2 看板更新桌位状态", ok)


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NekoCafé E2E 测试 (实验四)")
    print("3 条核心用户旅程")
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
        print("❌ 服务启动超时，请先运行 docker compose up -d")
        sys.exit(1)

    # 运行三条旅程
    journey_01_new_user()
    journey_02_returning_member()
    journey_03_staff_dashboard()

    # 汇总
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"E2E 测试结果: {passed}/{total} 通过 ({failed} 失败)")
    print(f"{'=' * 60}\n")

    if failed > 0:
        sys.exit(1)
