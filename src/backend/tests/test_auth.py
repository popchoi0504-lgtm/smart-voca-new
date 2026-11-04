# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 회원가입·로그인·로그아웃·내 정보 API 통합 테스트 (FR-AUTH-01~07, 인터페이스 정의서 4.2)
# 파일 위치: src/backend/tests/test_auth.py
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.core.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.core.timeutil import now_utc
from app.models.user import User

VALID_USER = {"email": "student@gmail.com", "password": "abcd1234"}


def signup(client, **overrides):
    return client.post("/api/auth/signup", json={**VALID_USER, **overrides})


def count_users(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(User))


# ---------- 회원가입 ----------


def test_signup_creates_user_and_logs_in(api_client, db_session):
    # When 올바른 정보로 가입하면
    response = signup(api_client)
    # Then 201, 회원 정보가 내려오고 비밀번호 관련 값은 없다
    assert response.status_code == 201
    user = response.json()["user"]
    assert user["email"] == "student@gmail.com"
    assert user["is_premium"] is False
    assert user["premium_until"] is None
    assert user["daily_new_limit"] == 10
    assert "password" not in response.text
    # And 로그인 쿠키가 HttpOnly, SameSite=Lax 로 내려온다
    set_cookie = response.headers["set-cookie"].lower()
    assert f"{ACCESS_TOKEN_COOKIE}=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    # And DB 에는 비밀번호 원문이 아니라 Argon2 해시가 저장된다
    saved = db_session.scalar(select(User))
    assert saved.password_hash.startswith("$argon2id$")
    assert "abcd1234" not in saved.password_hash
    # And 가입 직후 바로 로그인된 상태다
    assert api_client.get("/api/auth/me").status_code == 200


def test_signup_rejects_duplicate_email(api_client, db_session):
    signup(api_client)
    response = signup(api_client)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert count_users(db_session) == 1


def test_signup_normalizes_email_so_case_and_spaces_do_not_make_duplicates(api_client, db_session):
    assert signup(api_client, email="  Student@Gmail.COM ").status_code == 201
    assert db_session.scalar(select(User.email)) == "student@gmail.com"
    assert signup(api_client, email="STUDENT@gmail.com").status_code == 409


@pytest.mark.parametrize(
    "password, expected_message",
    [
        ("abc123", "8자 이상"),  # 너무 짧음
        ("abcdefgh", "영문과 숫자"),  # 숫자 없음
        ("12345678", "영문과 숫자"),  # 영문 없음
        ("a1" * 33, "64자 이하"),  # 66자: 너무 김
    ],
)
def test_signup_rejects_weak_password(api_client, db_session, password, expected_message):
    response = signup(api_client, password=password)
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["fields"][0]["field"] == "password"
    assert expected_message in body["fields"][0]["message"]
    assert count_users(db_session) == 0


@pytest.mark.parametrize("email", ["not-an-email", "a@b", "", "student@", "@gmail.com"])
def test_signup_rejects_bad_email(api_client, email):
    response = signup(api_client, email=email)
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "email"


def test_signup_reports_missing_fields_in_korean(api_client):
    response = api_client.post("/api/auth/signup", json={})
    assert response.status_code == 422
    fields = {item["field"]: item["message"] for item in response.json()["error"]["fields"]}
    assert fields == {"email": "필수 입력입니다.", "password": "필수 입력입니다."}


def test_form_encoded_request_is_rejected(api_client):
    # JSON 이 아닌 형식(HTML 폼)으로 보낸 요청은 받지 않는다 (다른 사이트가 몰래 보내는 요청 방어에 도움)
    response = api_client.post("/api/auth/login", data=VALID_USER)
    assert response.status_code == 422


# ---------- 로그인 ----------


def test_login_succeeds_with_right_credentials(api_client):
    signup(api_client)
    api_client.cookies.clear()  # 가입 때 받은 쿠키를 지워서 진짜 로그인부터 확인
    response = api_client.post("/api/auth/login", json=VALID_USER)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "student@gmail.com"
    assert api_client.get("/api/auth/me").status_code == 200


def test_login_ignores_case_and_spaces_in_email(api_client):
    signup(api_client)
    api_client.cookies.clear()
    response = api_client.post("/api/auth/login", json={"email": "  STUDENT@gmail.com ", "password": "abcd1234"})
    assert response.status_code == 200


def test_login_failures_do_not_reveal_which_part_was_wrong(api_client):
    signup(api_client)
    api_client.cookies.clear()
    wrong_password = api_client.post("/api/auth/login", json={**VALID_USER, "password": "wrong1234"})
    unknown_email = api_client.post("/api/auth/login", json={"email": "nobody@gmail.com", "password": "abcd1234"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()  # 응답이 완전히 똑같다
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert ACCESS_TOKEN_COOKIE not in wrong_password.headers.get("set-cookie", "")


def test_login_rejects_absurdly_long_input(api_client):
    response = api_client.post("/api/auth/login", json={"email": "a@gmail.com", "password": "x" * 500})
    assert response.status_code == 422


# ---------- 내 정보 / 로그아웃 / 보호 ----------


def test_me_requires_login(api_client):
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_logout_clears_login(api_client):
    signup(api_client)
    assert api_client.get("/api/auth/me").status_code == 200
    response = api_client.post("/api/auth/logout")
    assert response.status_code == 204
    assert api_client.get("/api/auth/me").status_code == 401


def test_logout_without_login_is_still_204(api_client):
    assert api_client.post("/api/auth/logout").status_code == 204


def test_tampered_cookie_is_rejected(api_client):
    signup(api_client)
    token = api_client.cookies.get(ACCESS_TOKEN_COOKIE)
    api_client.cookies.clear()
    api_client.cookies.set(ACCESS_TOKEN_COOKIE, token[:-2] + "xx")
    assert api_client.get("/api/auth/me").status_code == 401


def test_expired_cookie_is_rejected(api_client, db_session):
    signup(api_client)
    user_id = db_session.scalar(select(User.id))
    api_client.cookies.clear()
    api_client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(user_id, issued_at=now_utc() - timedelta(days=8)))
    assert api_client.get("/api/auth/me").status_code == 401


def test_cookie_of_a_deleted_user_is_rejected(api_client):
    # 유효한 증표라도 그 회원이 DB 에 없으면 통과시키지 않는다
    api_client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(999999))
    assert api_client.get("/api/auth/me").status_code == 401


def test_me_shows_premium_status_in_korean_time(api_client, db_session):
    signup(api_client)
    user = db_session.scalar(select(User))
    user.premium_until = now_utc() + timedelta(days=10)
    db_session.commit()
    premium = api_client.get("/api/auth/me").json()["user"]
    assert premium["is_premium"] is True
    assert premium["premium_until"].endswith("+09:00")  # 인터페이스 정의서: 한국 시간대로 내려 준다

    user.premium_until = now_utc() - timedelta(days=1)  # 이미 만료
    db_session.commit()
    expired = api_client.get("/api/auth/me").json()["user"]
    assert expired["is_premium"] is False
