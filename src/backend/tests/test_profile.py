# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필(닉네임·아바타)·비밀번호 변경·이용권 요약·회원 탈퇴 API 통합 테스트 (FR-PROFILE-01~05, 이슈 #17)
# 파일 위치: src/backend/tests/test_profile.py
import logging
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from consent_helpers import SIGNUP_CONSENT
from app.core.security import ACCESS_TOKEN_COOKIE
from app.core.timeutil import now_utc
from app.models.ai_usage import AiUsage
from app.models.payment import Payment
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word

EMAIL = "profile.person@gmail.com"
PASSWORD = "Abcd1234x"
NEW_PASSWORD = "Newpass5678"
CONFIRM = "탈퇴합니다"


@pytest.fixture
def client(api_client, db_session):
    db_session.add(Word(headword="alpha", part_of_speech="n.", meaning_ko="뜻", example_en="I see alpha.", example_ko="예문", frequency_rank=1))
    db_session.commit()
    assert api_client.post("/api/auth/signup", json={"email": EMAIL, "password": PASSWORD, **SIGNUP_CONSENT}).status_code == 201
    return api_client


def count(db_session, model) -> int:
    db_session.expire_all()
    return db_session.scalar(select(func.count()).select_from(model))


def me(client) -> dict:
    return client.get("/api/auth/me").json()["user"]


def withdraw(client, password=PASSWORD, confirm_text=CONFIRM):
    return client.post("/api/me/withdraw", json={"password": password, "confirm_text": confirm_text})


# ---------- 닉네임·아바타 (FR-PROFILE-01·02) ----------


def test_requires_login(api_client):
    assert api_client.patch("/api/me/profile", json={"nickname": "듀니"}).status_code == 401
    assert api_client.post("/api/me/password", json={"current_password": "a", "new_password": "b"}).status_code == 401
    assert api_client.get("/api/me/plan").status_code == 401
    assert api_client.post("/api/me/withdraw", json={"password": "a", "confirm_text": CONFIRM}).status_code == 401


def test_default_display_name_is_email_local_part_and_color_auto(client):
    user = me(client)
    assert user["nickname"] is None
    assert user["display_name"] == "profile.person"
    assert user["avatar_color"] in {"mint", "lavender", "yellow", "pink", "sky", "orange"}


def test_set_nickname_and_color(client):
    response = client.patch("/api/me/profile", json={"nickname": "  듀니  ", "avatar_color": "pink"})
    assert response.status_code == 200
    user = response.json()["user"]
    assert (user["nickname"], user["display_name"], user["avatar_color"]) == ("듀니", "듀니", "pink")
    assert me(client)["display_name"] == "듀니"  # 새로 읽어도 유지


def test_partial_update_changes_only_sent_field(client):
    client.patch("/api/me/profile", json={"nickname": "듀니", "avatar_color": "sky"})
    client.patch("/api/me/profile", json={"avatar_color": "mint"})
    user = me(client)
    assert (user["nickname"], user["avatar_color"]) == ("듀니", "mint")


@pytest.mark.parametrize("nickname", ["", "a", "   ", "a" * 13, "ab\ncd"])
def test_bad_nickname_rejected(client, nickname):
    response = client.patch("/api/me/profile", json={"nickname": nickname})
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "nickname"
    assert me(client)["nickname"] is None


@pytest.mark.parametrize("body", [{}, {"nickname": None}, {"avatar_color": "red"}, {"avatar_color": None}])
def test_bad_profile_body_rejected(client, body):
    assert client.patch("/api/me/profile", json=body).status_code == 422


def test_duplicate_nicknames_allowed(client):
    client.patch("/api/me/profile", json={"nickname": "듀니"})
    client.post("/api/auth/logout")
    client.post("/api/auth/signup", json={"email": "other@gmail.com", "password": PASSWORD, **SIGNUP_CONSENT})
    assert client.patch("/api/me/profile", json={"nickname": "듀니"}).status_code == 200


def test_db_blocks_unknown_color_even_if_code_forgets(db_session, client):
    from sqlalchemy.exc import IntegrityError

    user = db_session.scalar(select(User))
    user.avatar_color = "red"
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------- 비밀번호 변경 (FR-PROFILE-03) ----------


def test_change_password_success(client):
    response = client.post("/api/me/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert response.status_code == 204
    assert ACCESS_TOKEN_COOKIE in response.headers["set-cookie"]  # 이 기기는 새 증표
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": NEW_PASSWORD}).status_code == 200
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401


def test_change_password_wrong_current(client, db_session):
    before = db_session.scalar(select(User.password_hash))
    response = client.post("/api/me/password", json={"current_password": "Wrongpass1", "new_password": NEW_PASSWORD})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WRONG_PASSWORD"
    db_session.expire_all()
    assert db_session.scalar(select(User.password_hash)) == before


@pytest.mark.parametrize("new_password", ["short1", "onlyletters", "12345678", "a1" * 33, PASSWORD])
def test_change_password_new_rules(client, new_password):
    response = client.post("/api/me/password", json={"current_password": PASSWORD, "new_password": new_password})
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "new_password"


# ---------- 이용권 요약 (FR-PROFILE-04) ----------


def test_plan_summary_free_and_ai_usage(client, db_session):
    summary = client.get("/api/me/plan").json()
    assert summary == {"plan": "free", "premium_until": None, "ai_daily_limit": 10, "ai_used_today": 0, "ai_remaining_today": 10}
    from app.core.timeutil import today_kst

    user_id = db_session.scalar(select(User.id))
    db_session.add(AiUsage(user_id=user_id, usage_date=today_kst(), call_count=3))
    db_session.commit()
    summary = client.get("/api/me/plan").json()
    assert (summary["ai_used_today"], summary["ai_remaining_today"]) == (3, 7)


def test_plan_summary_premium(client, db_session):
    user = db_session.scalar(select(User))
    user.premium_until = now_utc() + timedelta(days=5)
    db_session.commit()
    summary = client.get("/api/me/plan").json()
    assert summary["plan"] == "premium"
    assert summary["premium_until"] is not None
    assert (summary["ai_daily_limit"], summary["ai_remaining_today"]) == (50, 50)


# ---------- 회원 탈퇴 (FR-PROFILE-05) ----------


def prepare_records(client, db_session):
    """학습 기록·AI 사용 횟수·결제 기록을 한 건씩 만든다."""
    from app.core.timeutil import today_kst

    assert client.post("/api/study/flashcard", json={"word_id": 1, "rating": "know"}).status_code == 200
    assert client.post("/api/payments/orders", json={"product": "premium_30d"}).status_code == 200
    user_id = db_session.scalar(select(User.id))
    db_session.add(AiUsage(user_id=user_id, usage_date=today_kst(), call_count=2))
    db_session.commit()
    assert count(db_session, UserWord) == 1 and count(db_session, ReviewLog) == 1
    assert count(db_session, AiUsage) == 1 and count(db_session, Payment) == 1


def test_withdraw_anonymizes_and_deletes_learning_records(client, db_session):
    prepare_records(client, db_session)
    client.patch("/api/me/profile", json={"nickname": "듀니", "avatar_color": "pink"})
    old_token = client.cookies.get(ACCESS_TOKEN_COOKIE)
    user_id = db_session.scalar(select(User.id))

    response = withdraw(client)
    assert response.status_code == 204

    # 학습 기록·AI 횟수는 삭제, 결제 기록은 남는다
    assert (count(db_session, UserWord), count(db_session, ReviewLog), count(db_session, AiUsage)) == (0, 0, 0)
    assert count(db_session, Payment) == 1
    # 회원 행은 누구인지 알 수 없다
    row = db_session.scalar(select(User))
    assert row.id == user_id
    assert row.email == f"deleted-{user_id}@deleted.invalid"
    assert row.password_hash == "!"
    assert (row.nickname, row.avatar_color, row.premium_until) == (None, None, None)
    assert row.deleted_at is not None
    assert db_session.scalar(select(Payment.user_id)) == user_id
    # 탈퇴 전에 받은 증표로는 더 이상 들어갈 수 없다(쿠키가 남은 다른 기기 상황)
    client.cookies.set(ACCESS_TOKEN_COOKIE, old_token)
    assert client.get("/api/auth/me").status_code == 401


def test_withdraw_logs_out_this_device(client):
    withdraw(client)
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401


def test_withdraw_wrong_password_changes_nothing(client, db_session):
    prepare_records(client, db_session)
    response = withdraw(client, password="Wrongpass1")
    assert response.status_code == 400 and response.json()["error"]["code"] == "WRONG_PASSWORD"
    assert count(db_session, UserWord) == 1 and count(db_session, Payment) == 1
    assert db_session.scalar(select(User.email)) == EMAIL
    assert client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize("confirm_text", ["", "탈퇴", "탈퇴합니다!", "withdraw"])
def test_withdraw_wrong_confirm_text(client, db_session, confirm_text):
    prepare_records(client, db_session)
    response = withdraw(client, confirm_text=confirm_text)
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "confirm_text"
    assert count(db_session, UserWord) == 1
    assert db_session.scalar(select(User.deleted_at)) is None


def test_deleted_member_cannot_log_in_and_email_can_signup_again(client, db_session):
    withdraw(client)
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    assert client.post("/api/auth/login", json={"email": f"deleted-1@deleted.invalid", "password": "!"}).status_code == 401
    # 같은 이메일로 다시 가입: 새 회원, 옛 기록과 이어지지 않는다
    response = client.post("/api/auth/signup", json={"email": EMAIL, "password": "Another123", **SIGNUP_CONSENT})
    assert response.status_code == 201
    assert response.json()["user"]["id"] != 1
    assert count(db_session, User) == 2


def test_withdraw_leaves_other_members_untouched(client, db_session):
    assert client.post("/api/study/flashcard", json={"word_id": 1, "rating": "know"}).status_code == 200
    client.post("/api/auth/logout")
    client.post("/api/auth/signup", json={"email": "second@gmail.com", "password": PASSWORD, **SIGNUP_CONSENT})
    client.post("/api/study/flashcard", json={"word_id": 1, "rating": "know"})
    client.patch("/api/me/profile", json={"nickname": "둘째"})
    assert withdraw(client).status_code == 204
    # 첫 번째 회원의 기록과 정보는 그대로
    assert count(db_session, UserWord) == 1
    first = db_session.scalar(select(User).where(User.id == 1))
    assert first.email == EMAIL and first.deleted_at is None


# ---------- 로그 안전 (NFR-PROFILE-01) ----------


def test_logs_contain_no_password_or_email(client, caplog):
    caplog.set_level(logging.DEBUG)
    client.patch("/api/me/profile", json={"nickname": "비밀닉네임"})
    client.post("/api/me/password", json={"current_password": "Wrongpass1", "new_password": NEW_PASSWORD})  # 실패
    client.post("/api/me/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    withdraw(client, password="Wrongpass2")  # 실패
    withdraw(client, password=NEW_PASSWORD)
    text = "\n".join(record.getMessage() for record in caplog.records)
    for secret in (PASSWORD, NEW_PASSWORD, "Wrongpass1", "Wrongpass2", EMAIL, "profile.person", "비밀닉네임"):
        assert secret not in text, f"로그에 {secret!r} 이 남았습니다"
    assert "user_id=1" in text  # 회원 번호로는 추적할 수 있다
