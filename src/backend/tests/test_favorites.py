# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 즐겨찾기 API 통합 테스트 (담기·해제·목록·잠금·다시 학습, 이슈 #22)
# 파일 위치: src/backend/tests/test_favorites.py
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from consent_helpers import SIGNUP_CONSENT
from app.core.timeutil import now_utc
from app.models.favorite import Favorite
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}
OTHER_CREDENTIALS = {"email": "other@gmail.com", "password": "abcd1234"}
FREE_LIMIT = 250
WORD_COUNT = 260  # 무료 범위(250)를 넘는 단어까지 준비


@pytest.fixture
def words(db_session):
    db_session.add_all(
        Word(headword=f"word{rank:03d}", part_of_speech="n.", meaning_ko=f"뜻{rank}", example_en=f"I see word{rank:03d}.",
             example_ko=f"나는 {rank}를 본다.", frequency_rank=rank)
        for rank in range(1, WORD_COUNT + 1)
    )
    db_session.commit()


@pytest.fixture
def client(api_client, words):
    assert api_client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    return api_client


def set_premium_until(db_session, moment):
    user = db_session.scalar(select(User).where(User.email == CREDENTIALS["email"]))
    user.premium_until = moment
    db_session.commit()


def favorite_count(db_session):
    return db_session.scalar(select(func.count()).select_from(Favorite))


def test_add_and_list(client, db_session):
    assert client.put("/api/favorites/3").status_code == 204
    assert client.put("/api/favorites/5").status_code == 204
    body = client.get("/api/favorites").json()
    assert body["total_count"] == 2
    assert [item["word_id"] for item in body["items"]] == [5, 3]  # 최근에 단 순
    assert body["items"][0]["headword"] == "word005"
    assert body["items"][0]["is_locked"] is False


def test_add_twice_keeps_one_row(client, db_session):
    assert client.put("/api/favorites/3").status_code == 204
    assert client.put("/api/favorites/3").status_code == 204  # 이미 켜져 있어도 성공
    assert favorite_count(db_session) == 1


def test_remove_and_remove_again(client, db_session):
    client.put("/api/favorites/3")
    assert client.delete("/api/favorites/3").status_code == 204
    assert favorite_count(db_session) == 0
    assert client.delete("/api/favorites/3").status_code == 204  # 없어도 성공
    assert client.get("/api/favorites").json()["total_count"] == 0


def test_unknown_word_is_404(client):
    response = client.put("/api/favorites/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORD_NOT_FOUND"


def test_locked_word_cannot_be_added_on_free_plan(client, db_session):
    response = client.put(f"/api/favorites/{FREE_LIMIT + 1}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PLAN_LIMIT_EXCEEDED"
    assert favorite_count(db_session) == 0
    assert client.put(f"/api/favorites/{FREE_LIMIT}").status_code == 204  # 경계값은 허용


def test_premium_can_add_all_words(client, db_session):
    set_premium_until(db_session, now_utc() + timedelta(days=30))
    assert client.put(f"/api/favorites/{WORD_COUNT}").status_code == 204


def test_expired_premium_keeps_favorite_but_locked(client, db_session):
    set_premium_until(db_session, now_utc() + timedelta(days=30))
    client.put(f"/api/favorites/{WORD_COUNT}")
    client.put("/api/favorites/1")
    set_premium_until(db_session, now_utc() - timedelta(days=1))  # 이용권 만료
    items = {item["word_id"]: item for item in client.get("/api/favorites").json()["items"]}
    assert items[WORD_COUNT]["is_locked"] is True
    assert items[1]["is_locked"] is False
    study = client.get("/api/favorites/study").json()
    assert [item["word_id"] for item in study["items"]] == [1]  # 잠긴 단어는 다시 학습에서 빠진다
    assert study["total_available"] == 1
    assert client.delete(f"/api/favorites/{WORD_COUNT}").status_code == 204  # 해제는 가능
    assert favorite_count(db_session) == 1


def test_favorites_are_per_user(client, db_session):
    client.put("/api/favorites/3")
    client.post("/api/auth/logout")
    assert client.post("/api/auth/signup", json={**OTHER_CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    assert client.get("/api/favorites").json()["total_count"] == 0
    client.delete("/api/favorites/3")  # 남의 별표는 지워지지 않는다
    assert favorite_count(db_session) == 1


def test_study_returns_card_fields_and_respects_limit(client):
    for word_id in range(1, 8):
        client.put(f"/api/favorites/{word_id}")
    body = client.get("/api/favorites/study?limit=3").json()
    assert len(body["items"]) == 3
    assert body["total_available"] == 7
    assert set(body["items"][0]) >= {"word_id", "headword", "meaning_ko", "example_en", "example_ko"}
    assert client.get("/api/favorites/study?limit=21").status_code == 422


def test_study_does_not_touch_learning_records(client, db_session):
    client.put("/api/favorites/1")
    client.get("/api/favorites/study")
    assert db_session.scalar(select(func.count()).select_from(UserWord)) == 0
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 0


def test_requires_login(api_client, words):
    assert api_client.get("/api/favorites").status_code == 401
    assert api_client.put("/api/favorites/1").status_code == 401
    assert api_client.delete("/api/favorites/1").status_code == 401
    assert api_client.get("/api/favorites/study").status_code == 401
