"""
会员服务单元测试
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
        assert data["service"] == "member"


class TestMemberCRUD:
    def test_create_member(self):
        payload = {
            "name": "张三",
            "phone": "13800138001",
            "email": "zhangsan@example.com",
            "birthday": "1995-06-15",
            "favorite_cat_breeds": ["英短", "布偶"],
        }
        response = client.post("/api/v1/members", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "张三"
        assert data["tier"] == "bronze"
        assert data["points"] == 0
        assert "id" in data

    def test_create_member_invalid_phone(self):
        payload = {
            "name": "李四",
            "phone": "12345",
        }
        response = client.post("/api/v1/members", json=payload)
        assert response.status_code == 422

    def test_get_member_not_found(self):
        response = client.get("/api/v1/members/non-existent-id")
        assert response.status_code == 404

    def test_update_member(self):
        # 先创建
        payload = {
            "name": "王五",
            "phone": "13800138002",
        }
        create_resp = client.post("/api/v1/members", json=payload)
        member_id = create_resp.json()["id"]

        # 再更新
        update_payload = {"name": "王五改", "email": "wangwu@example.com"}
        update_resp = client.patch(f"/api/v1/members/{member_id}", json=update_payload)
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "王五改"
        assert update_resp.json()["email"] == "wangwu@example.com"

    def test_list_members(self):
        response = client.get("/api/v1/members")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_by_tier(self):
        response = client.get("/api/v1/members?tier=bronze")
        assert response.status_code == 200


class TestTracing:
    def test_trace_id_in_response_header(self):
        response = client.get("/health")
        assert "X-Trace-Id" in response.headers
