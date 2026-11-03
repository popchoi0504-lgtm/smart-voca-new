# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - /api/health 와 공통 오류 응답 모양 테스트 (VS-0, FR-SYS-01)
# 파일 위치: src/backend/tests/test_health.py
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


class BrokenSession:
    """DB 가 고장 난 상황을 흉내 내는 가짜 세션: 무엇을 시켜도 오류를 낸다."""

    def execute(self, *args, **kwargs):
        raise RuntimeError("DB 연결 실패 흉내")

    def close(self):
        pass


def broken_db():
    yield BrokenSession()


@pytest.fixture
def client():
    return TestClient(app)


def test_health_ok_when_db_is_up(client):
    # Given 서버와 DB 가 정상이다
    # When 상태 확인을 요청하면
    response = client.get("/api/health")
    # Then 200 과 함께 서버·DB 모두 ok 이다
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_returns_503_when_db_is_down(client):
    # Given DB 가 고장 났다 (가짜 세션으로 교체)
    app.dependency_overrides[get_db] = broken_db
    try:
        # When 상태 확인을 요청하면
        response = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()
    # Then 503 이고 정해진 모양으로 알려 준다 (내부 오류 내용은 응답에 없다)
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "error"}


def test_unknown_route_uses_standard_error_shape(client):
    # When 없는 주소로 요청하면
    response = client.get("/api/does-not-exist")
    # Then 404 이고 공통 오류 모양({"error": {"code", "message"}}) 이다
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "message" in body["error"]


def test_wrong_method_uses_standard_error_shape(client):
    # When 허용되지 않은 방식(POST)으로 요청하면
    response = client.post("/api/health")
    # Then 405 이고 공통 오류 모양이다
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
