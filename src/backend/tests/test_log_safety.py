# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 로그·오류 응답에 비밀번호·토큰·결제키·비밀값이 새지 않는지 검사 (NFR-SEC-03, 구현 계획서 VS-7)
# 파일 위치: src/backend/tests/test_log_safety.py
# 방식: 가입·로그인(성공/실패)·결제(승인/거절/통신 실패)·예상 못 한 서버 오류를 한 번씩 일으키고,
#       그동안 남은 모든 로그 문장에 "새면 안 되는 값"이 한 번이라도 들어 있는지 찾는다.
import logging

import pytest
from fastapi.testclient import TestClient

from consent_helpers import SIGNUP_CONSENT
from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN_COOKIE
from app.main import app
from app.models.word import Word
from app.payments.fake_provider import FakePaymentProvider
from app.payments.provider import get_payment_provider

PASSWORD = "Zq9-unique-pass-123"
WRONG_PASSWORD = "Wr0ng-unique-pass-456"
EMAIL = "logcheck.person@gmail.com"
PAYMENT_KEY = "pk_secret_marker_777"


@pytest.fixture
def forbidden_values():
    """로그에 나오면 안 되는 값 목록. 이름을 붙여 두면 실패했을 때 무엇이 샜는지 바로 보인다."""
    settings = get_settings()
    values = {
        "비밀번호": PASSWORD,
        "틀린 비밀번호": WRONG_PASSWORD,
        "결제키": PAYMENT_KEY,
        "JWT 비밀값": settings.jwt_secret,
    }
    if settings.toss_secret_key:
        values["토스 시크릿 키"] = settings.toss_secret_key
    return values


@pytest.fixture
def fake_provider():
    fake = FakePaymentProvider()
    app.dependency_overrides[get_payment_provider] = lambda: fake
    return fake


def all_log_text(caplog) -> str:
    return "\n".join(record.getMessage() for record in caplog.records)


def test_normal_flow_logs_contain_no_secrets(api_client, db_session, caplog, forbidden_values, fake_provider):
    caplog.set_level(logging.DEBUG)
    db_session.add(Word(headword="alpha", part_of_speech="n.", meaning_ko="뜻", example_en="I see alpha.", example_ko="예문", frequency_rank=1))
    db_session.commit()

    # 가입 → 로그아웃 → 틀린 비밀번호 → 없는 이메일 → 올바른 로그인
    api_client.post("/api/auth/signup", json={"email": EMAIL, "password": PASSWORD, **SIGNUP_CONSENT})
    token = api_client.cookies.get(ACCESS_TOKEN_COOKIE)
    forbidden_values["로그인 토큰"] = token
    api_client.post("/api/auth/logout")
    assert api_client.post("/api/auth/login", json={"email": EMAIL, "password": WRONG_PASSWORD}).status_code == 401
    assert api_client.post("/api/auth/login", json={"email": "nobody.here@gmail.com", "password": WRONG_PASSWORD}).status_code == 401
    assert api_client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 200

    # 결제: 승인, 거절, 통신 실패
    for outcome in ("approve", "reject", "unavailable"):
        fake_provider.outcome = outcome
        placed = api_client.post("/api/payments/orders", json={"product": "premium_30d"}).json()
        api_client.post("/api/payments/confirm", json={"payment_key": PAYMENT_KEY, "order_id": placed["order_id"], "amount": placed["amount"]})

    text = all_log_text(caplog)
    assert "로그인 실패" in text and "결제 승인" in text  # 검사 대상 로그가 실제로 남았는지(빈 로그면 검사가 무의미)
    leaked = [name for name, value in forbidden_values.items() if value and value in text]
    assert leaked == []


def test_login_failure_log_masks_email(api_client, caplog):
    caplog.set_level(logging.INFO)
    api_client.post("/api/auth/login", json={"email": "nobody.here@gmail.com", "password": WRONG_PASSWORD})
    text = all_log_text(caplog)
    assert "로그인 실패(가입되지 않은 이메일)" in text
    assert "nobody.here" not in text


def test_unexpected_error_hides_details_from_response_but_is_logged(api_client, monkeypatch, caplog):
    """예상 못 한 오류: 응답에는 일반 문장만, 원인은 로그에만 남는다."""
    caplog.set_level(logging.INFO)

    def explode(*args, **kwargs):
        raise RuntimeError("INTERNAL-DETAIL-postgresql://user:pw@host/db")

    monkeypatch.setattr("app.routers.auth.auth_service.signup", explode)
    with TestClient(app, raise_server_exceptions=False) as lenient_client:
        # api_client 가 DB 를 테스트 DB 로 바꿔 둔 상태(dependency_overrides)를 그대로 쓴다
        response = lenient_client.post("/api/auth/signup", json={"email": EMAIL, "password": PASSWORD, **SIGNUP_CONSENT})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    for hidden in ("INTERNAL-DETAIL", "postgresql://", "Traceback", "RuntimeError", PASSWORD):
        assert hidden not in response.text
    assert "처리되지 않은 오류" in all_log_text(caplog)
