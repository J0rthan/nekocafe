"""
预约服务 - 契约测试 (Consumer-Driven Contract Tests)

3对消费者-提供者:
1. Member Service → Reservation Service (查询预约列表)
2. Member Service → Reservation Service (创建预约)
3. Gateway/Web → Reservation Service (查询桌位)
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


# ============================================================
# Contract Pair 1: Member → Reservation (GET /reservations?customer_id=)
# ============================================================
class TestContractListReservations:
    """
    契约: Member Service 调用 Reservation Service 查询某会员的预约
    预期: 返回 200 + List[ReservationResponse]
    """

    def test_contract_list_returns_array(self):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.fixture
    def reservation_id(self):
        client = TestClient(app)
        resp = client.post("/api/v1/reservations", json={
            "customer_id": "cust-contract-001",
            "store_id": "store-001",
            "table_id": "tbl-001",
            "reservation_time": "2026-07-01T18:00:00",
            "guest_count": 2,
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_contract_filter_by_customer(self, reservation_id):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations?customer_id=cust-contract-001")
        assert resp.status_code == 200
        data = resp.json()
        for r in data:
            assert r["customer_id"] == "cust-contract-001"

    def test_contract_reservation_structure(self, reservation_id):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations?customer_id=cust-contract-001")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        r = data[0]
        # 契约字段验证
        assert "id" in r
        assert "customer_id" in r
        assert "store_id" in r
        assert "table_id" in r
        assert "reservation_time" in r
        assert "guest_count" in r
        assert "status" in r
        assert "created_at" in r
        assert r["status"] in ("pending", "confirmed", "cancelled", "completed")


# ============================================================
# Contract Pair 2: Member → Reservation (POST /reservations)
# ============================================================
class TestContractCreateReservation:
    """
    契约: Member Service 调用 Reservation Service 创建预约
    预期: 返回 201 + ReservationResponse
    """

    def test_contract_create_returns_201(self):
        client = TestClient(app)
        payload = {
            "customer_id": "cust-contract-create",
            "store_id": "store-001",
            "table_id": "tbl-005",
            "reservation_time": "2026-07-15T12:00:00",
            "guest_count": 3,
            "notes": "Contract test",
        }
        resp = client.post("/api/v1/reservations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["customer_id"] == payload["customer_id"]
        assert data["guest_count"] == 3
        assert data["status"] == "pending"

    def test_contract_create_invalid_returns_422(self):
        client = TestClient(app)
        resp = client.post("/api/v1/reservations", json={
            "customer_id": "test",
            # missing required fields
        })
        assert resp.status_code == 422


# ============================================================
# Contract Pair 3: Gateway → Reservation (GET /reservations/tables)
# ============================================================
class TestContractListTables:
    """
    契约: API Gateway / Web 前端调用 Reservation Service 查询桌位
    预期: 返回 200 + List[TableInfo]
    """

    def test_contract_tables_returns_array(self):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations/tables")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_contract_table_structure(self):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations/tables")
        assert resp.status_code == 200
        t = resp.json()[0]
        assert "id" in t
        assert "store_id" in t
        assert "table_number" in t
        assert "capacity" in t
        assert "is_available" in t
        assert "cat_friendly" in t
        assert isinstance(t["capacity"], int)
        assert isinstance(t["is_available"], bool)
        assert isinstance(t["cat_friendly"], bool)

    def test_contract_available_only_filter(self):
        client = TestClient(app)
        resp = client.get("/api/v1/reservations/tables?available_only=true")
        assert resp.status_code == 200
        for t in resp.json():
            assert t["is_available"] is True
