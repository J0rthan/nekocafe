"""
预约服务单元测试
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reservation"


class TestTableList:
    def test_list_all_tables(self):
        response = client.get("/api/v1/reservations/tables")
        assert response.status_code == 200
        tables = response.json()
        assert len(tables) > 0
        assert "id" in tables[0]
        assert "capacity" in tables[0]

    def test_filter_by_store(self):
        response = client.get("/api/v1/reservations/tables?store_id=store-002")
        assert response.status_code == 200
        tables = response.json()
        for t in tables:
            assert t["store_id"] == "store-002"

    def test_filter_available_only(self):
        response = client.get("/api/v1/reservations/tables?available_only=true")
        assert response.status_code == 200
        tables = response.json()
        for t in tables:
            assert t["is_available"] is True


class TestReservationCRUD:
    def test_create_reservation(self):
        payload = {
            "customer_id": "cust-001",
            "store_id": "store-001",
            "table_id": "tbl-001",
            "reservation_time": "2026-06-01T18:00:00",
            "guest_count": 4,
            "notes": "靠窗位置",
        }
        response = client.post("/api/v1/reservations", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == "cust-001"
        assert data["status"] == "pending"
        assert "id" in data

    def test_get_reservation_not_found(self):
        response = client.get("/api/v1/reservations/non-existent-id")
        assert response.status_code == 404

    def test_cancel_reservation(self):
        # 先创建
        payload = {
            "customer_id": "cust-002",
            "store_id": "store-001",
            "table_id": "tbl-002",
            "reservation_time": "2026-06-02T19:00:00",
            "guest_count": 2,
        }
        create_resp = client.post("/api/v1/reservations", json=payload)
        reservation_id = create_resp.json()["id"]

        # 再取消
        cancel_resp = client.patch(f"/api/v1/reservations/{reservation_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

    def test_list_reservations_by_customer(self):
        response = client.get("/api/v1/reservations?customer_id=cust-001")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTracing:
    def test_trace_id_in_response_header(self):
        response = client.get("/health")
        assert "X-Trace-Id" in response.headers
