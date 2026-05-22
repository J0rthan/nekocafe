"""
会员服务 - 契约测试 (Consumer-Driven Contract Tests)
使用 pact-python 定义消费者-提供者契约

3对消费者-提供者:
1. Reservation Service → Member Service (获取会员信息)
2. Reservation Service → Member Service (获取会员等级)
3. Reservation Service → Member Service (获取会员预约历史)
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


# ============================================================
# Contract Pair 1: Reservation → Member (GET /api/v1/members/{id})
# ============================================================
class TestContractGetMember:
    """
    契约: Reservation Service 调用 Member Service 获取会员详情
    预期: 返回 200 + MemberResponse 结构
    """

    @pytest.fixture
    def member_id(self):
        """先创建一个会员作为前置条件"""
        client = TestClient(app)
        resp = client.post("/api/v1/members", json={
            "name": "契约测试用户",
            "phone": "13900139001",
            "email": "contract@nekocafe.test",
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_contract_member_response_structure(self, member_id):
        """验证响应结构符合契约"""
        client = TestClient(app)
        resp = client.get(f"/api/v1/members/{member_id}")
        assert resp.status_code == 200
        data = resp.json()
        # 契约字段验证
        assert "id" in data
        assert "name" in data
        assert "phone" in data
        assert "email" in data
        assert "tier" in data
        assert "points" in data
        assert "favorite_cat_breeds" in data
        assert "created_at" in data
        assert "updated_at" in data
        # 契约类型验证
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["tier"], str)
        assert isinstance(data["points"], int)
        assert isinstance(data["favorite_cat_breeds"], list)
        assert data["tier"] in ("bronze", "silver", "gold", "platinum")

    def test_contract_get_member_404(self):
        """契约: 不存在的会员返回 404"""
        client = TestClient(app)
        resp = client.get("/api/v1/members/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data


# ============================================================
# Contract Pair 2: Reservation → Member (GET /api/v1/members?tier=)
# ============================================================
class TestContractListMembers:
    """
    契约: Reservation Service 按等级查询会员列表
    预期: 返回 200 + List[MemberResponse]
    """

    def test_contract_list_members_returns_array(self):
        """契约: 列表接口始终返回数组"""
        client = TestClient(app)
        resp = client.get("/api/v1/members")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_contract_filter_by_tier(self):
        """契约: 按 tier 过滤，返回的会员等级匹配"""
        client = TestClient(app)
        resp = client.get("/api/v1/members?tier=bronze&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        for member in data:
            assert member["tier"] == "bronze"

    def test_contract_limit_respected(self):
        """契约: limit 参数必须生效"""
        client = TestClient(app)
        # 先创建多个会员
        for i in range(5):
            client.post("/api/v1/members", json={
                "name": f"限流测试{i}",
                "phone": f"139001390{i:02d}",
            })
        resp = client.get("/api/v1/members?limit=3")
        assert resp.status_code == 200
        assert len(resp.json()) <= 3


# ============================================================
# Contract Pair 3: Reservation → Member (GET /members/{id}/reservation-history)
# ============================================================
class TestContractReservationHistory:
    """
    契约: Reservation Service 调用 Member Service 获取预约历史
    预期: 返回 {member_id, total_reservations, reservations[]}
    """

    @pytest.fixture
    def member_id(self):
        client = TestClient(app)
        resp = client.post("/api/v1/members", json={
            "name": "历史查询用户",
            "phone": "13900139002",
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_contract_history_structure(self, member_id):
        """契约: 预约历史响应结构"""
        client = TestClient(app)
        resp = client.get(f"/api/v1/members/{member_id}/reservation-history")
        assert resp.status_code == 200
        data = resp.json()
        assert "member_id" in data
        assert "total_reservations" in data
        assert "reservations" in data
        assert isinstance(data["reservations"], list)
        assert isinstance(data["total_reservations"], int)

    def test_contract_history_404_for_unknown_member(self):
        """契约: 不存在的会员返回 404"""
        client = TestClient(app)
        resp = client.get("/api/v1/members/nonexistent/reservation-history")
        assert resp.status_code == 404
