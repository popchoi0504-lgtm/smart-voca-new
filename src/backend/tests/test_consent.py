# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 가입 동의(필수 3·선택 1)·약관 버전 대조·마케팅 동의 변경 API 통합 테스트 (FR-CONSENT-01~04, 이슈 #18)
# 파일 위치: src/backend/tests/test_consent.py
import logging
from pathlib import Path

import pytest
from consent_helpers import SIGNUP_CONSENT
from sqlalchemy import func, select

from app.core_logic.consent_rules import TERMS_VERSION
from app.models.user import User

EMAIL = "consent.person@gmail.com"
PASSWORD = "Abcd1234x"
CREDENTIALS = {"email": EMAIL, "password": PASSWORD}


def signup(client, **overrides):
    return client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT, **overrides})


def count_users(db_session) -> int:
    db_session.expire_all()
    return db_session.scalar(select(func.count()).select_from(User))


def test_signup_records_consent_time_and_version(api_client, db_session):
    response = signup(api_client)
    assert response.status_code == 201
    assert response.json()["user"]["marketing_agreed"] is False
    user = db_session.scalar(select(User))
    assert user.terms_agreed_at is not None
    assert user.terms_version == TERMS_VERSION
    assert user.marketing_agreed is False


def test_marketing_opt_in_is_saved(api_client, db_session):
    assert signup(api_client, agree_marketing=True).json()["user"]["marketing_agreed"] is True
    assert db_session.scalar(select(User.marketing_agreed)) is True


@pytest.mark.parametrize("field", ["agree_age", "agree_terms", "agree_privacy"])
@pytest.mark.parametrize("value", [False, None, "false", 0])
def test_each_required_consent_is_enforced(api_client, db_session, field, value):
    response = signup(api_client, **{field: value})
    assert response.status_code == 422
    assert field in {item["field"] for item in response.json()["error"]["fields"]}
    assert count_users(db_session) == 0  # 회원이 만들어지지 않는다


@pytest.mark.parametrize("field", ["agree_age", "agree_terms", "agree_privacy", "terms_version"])
def test_missing_consent_field_rejected(api_client, db_session, field):
    body = {**CREDENTIALS, **SIGNUP_CONSENT}
    del body[field]
    assert api_client.post("/api/auth/signup", json=body).status_code == 422
    assert count_users(db_session) == 0


def test_wrong_terms_version_is_conflict(api_client, db_session):
    response = signup(api_client, terms_version="1999-01-01")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TERMS_VERSION_MISMATCH"
    assert count_users(db_session) == 0


def test_login_response_includes_marketing_flag(api_client):
    signup(api_client, agree_marketing=True)
    api_client.post("/api/auth/logout")
    response = api_client.post("/api/auth/login", json=CREDENTIALS)
    assert response.json()["user"]["marketing_agreed"] is True


def test_marketing_consent_can_be_changed_and_withdrawn(api_client, db_session):
    signup(api_client)
    assert api_client.patch("/api/me/consent", json={"marketing_agreed": True}).json()["user"]["marketing_agreed"] is True
    assert api_client.patch("/api/me/consent", json={"marketing_agreed": False}).json()["user"]["marketing_agreed"] is False
    assert db_session.scalar(select(User.marketing_agreed)) is False


def test_consent_change_requires_login_and_valid_body(api_client):
    assert api_client.patch("/api/me/consent", json={"marketing_agreed": True}).status_code == 401
    signup(api_client)
    assert api_client.patch("/api/me/consent", json={}).status_code == 422
    # 필수 동의 항목은 이 API 로 바꿀 수 없다(무시되지 않고 아무 일도 안 일어남)
    assert api_client.patch("/api/me/consent", json={"marketing_agreed": True, "agree_terms": False}).status_code == 200


def test_withdraw_keeps_consent_proof_but_clears_marketing(api_client, db_session):
    signup(api_client, agree_marketing=True)
    response = api_client.post("/api/me/withdraw", json={"password": PASSWORD, "confirm_text": "탈퇴합니다"})
    assert response.status_code == 204
    db_session.expire_all()
    user = db_session.scalar(select(User))
    assert user.terms_agreed_at is not None and user.terms_version == TERMS_VERSION  # 동의 증빙은 남김
    assert user.marketing_agreed is False


def test_server_and_frontend_terms_versions_match():
    """서버 상수와 화면 상수가 어긋나면 가입이 전부 409 가 되므로 파일 내용을 직접 비교해 막는다."""
    version_file = Path(__file__).resolve().parents[2] / "frontend" / "src" / "legal" / "version.js"
    assert f"'{TERMS_VERSION}'" in version_file.read_text(encoding="utf-8")


def test_logs_contain_no_email_for_consent_flow(api_client, caplog):
    caplog.set_level(logging.DEBUG)
    signup(api_client, agree_marketing=True)
    signup(api_client, terms_version="1999-01-01", email="other.person@gmail.com")
    api_client.patch("/api/me/consent", json={"marketing_agreed": False})
    text = "\n".join(record.getMessage() for record in caplog.records)
    for secret in (EMAIL, "consent.person", "other.person", PASSWORD):
        assert secret not in text
    assert "user_id=1" in text
