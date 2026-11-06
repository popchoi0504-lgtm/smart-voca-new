# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 오늘 할 것·새 단어·플래시카드·설정 API 통합 테스트 (FR-STUDY-01~06, FR-SRS-01~03, 구현 계획서 VS-3)
# 파일 위치: src/backend/tests/test_study.py
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from consent_helpers import SIGNUP_CONSENT
from app.core.timeutil import now_utc
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}
FREE_LIMIT = 250  # 설정 free_word_limit 기본값
WORD_COUNT = 260  # 무료 범위(250)를 넘는 단어까지 준비


@pytest.fixture
def words(db_session):
    """순위 1~260 의 가짜 단어 260개 (word_id 는 순위와 같다: RESTART IDENTITY)."""
    db_session.add_all(
        Word(headword=f"word{rank:03d}", part_of_speech="n.", meaning_ko=f"뜻{rank}", example_en=f"I see word{rank:03d}.",
             example_ko=f"나는 {rank}를 본다.", frequency_rank=rank)
        for rank in range(1, WORD_COUNT + 1)
    )
    db_session.commit()


@pytest.fixture
def client(api_client, words):
    """가입(=로그인)까지 끝낸 가짜 브라우저."""
    assert api_client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    return api_client


@pytest.fixture
def clock(monkeypatch):
    """서비스가 보는 "지금"을 테스트에서 옮기는 장치. clock.advance(days=1) 이면 하루 뒤가 된다."""

    class Clock:
        offset = timedelta(0)

        def advance(self, **kwargs):
            self.offset += timedelta(**kwargs)

    fake = Clock()
    monkeypatch.setattr("app.services.study_service.now_utc", lambda: now_utc() + fake.offset)
    return fake


def make_premium(db_session):
    user = db_session.scalar(select(User))
    user.premium_until = now_utc() + timedelta(days=30)
    db_session.commit()


def rate(client, word_id, rating="know"):
    return client.post("/api/study/flashcard", json={"word_id": word_id, "rating": rating})


# ---------- 로그인 필요 ----------


@pytest.mark.parametrize("method,path", [("get", "/api/study/today"), ("get", "/api/study/new"),
                                          ("post", "/api/study/flashcard"), ("patch", "/api/me/settings")])
def test_requires_login(api_client, method, path):
    assert getattr(api_client, method)(path).status_code == 401


# ---------- 오늘 할 것 ----------


def test_today_for_new_user(client):
    body = client.get("/api/study/today").json()
    assert body["review_due_count"] == 0
    assert body["new_target_count"] == 10
    assert body["new_learned_today"] == 0
    assert body["daily_new_limit"] == 10
    assert body["plan_word_limit"] == FREE_LIMIT
    assert body["new_locked_by_plan"] is False


# ---------- 새 단어 ----------


def test_new_words_come_in_rank_order(client):
    items = client.get("/api/study/new").json()["items"]
    assert [item["frequency_rank"] for item in items] == list(range(1, 11))
    assert set(items[0]) == {"word_id", "headword", "part_of_speech", "meaning_ko", "example_en", "example_ko", "frequency_rank"}


def test_new_words_skip_learned_ones(client):
    rate(client, 1)
    rate(client, 2)
    items = client.get("/api/study/new?limit=3").json()["items"]
    assert [item["frequency_rank"] for item in items] == [3, 4, 5]


@pytest.mark.parametrize("bad_limit", [0, 11, "abc"])
def test_new_words_limit_validation(client, bad_limit):
    assert client.get(f"/api/study/new?limit={bad_limit}").status_code == 422


# ---------- 플래시카드: 핵심 완료 기준 ----------


def test_rating_ten_new_words_saves_state_and_logs_and_next_day_they_are_due(client, db_session, clock):
    # Given 새 단어 10개를 모두 "알았음"으로 평가하면
    for word in client.get("/api/study/new").json()["items"]:
        response = rate(client, word["word_id"], "know")
        assert response.status_code == 200
    # Then user_words 10행(첫 간격 1일, 점수 5)과 review_logs 10행이 생긴다
    assert db_session.scalar(select(func.count()).select_from(UserWord)) == 10
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 10
    saved = db_session.get(UserWord, (1, 1))
    assert (saved.repetitions, saved.interval_days, saved.ease_factor) == (1, 1, Decimal("2.60"))
    log = db_session.scalar(select(ReviewLog).where(ReviewLog.word_id == 1))
    assert (log.activity_type, log.result, log.sm2_quality, log.max_hint_level) == ("flashcard", "know", 5, 0)
    # And 오늘은 복습 대상이 없고, 새 단어 목표를 채웠다
    today = client.get("/api/study/today").json()
    assert (today["review_due_count"], today["new_learned_today"], today["new_target_count"]) == (0, 10, 0)
    assert client.get("/api/study/new").json()["items"] == []
    # When 하루가 지나면
    clock.advance(days=1)
    # Then 10개가 복습 대상이 되고, 새 단어 10개를 다시 배울 수 있다
    next_day = client.get("/api/study/today").json()
    assert (next_day["review_due_count"], next_day["new_learned_today"], next_day["new_target_count"]) == (10, 0, 10)


def test_response_has_next_review_date(client):
    body = rate(client, 1, "know").json()
    today = client.get("/api/study/today").json()["today"]
    assert body["sm2_quality"] == 5
    assert body["interval_days"] == 1
    assert body["next_review_date"] > today  # 내일


@pytest.mark.parametrize("rating,quality", [("dont_know", 1), ("unsure", 3), ("know", 5)])
def test_rating_is_converted_to_quality(client, db_session, rating, quality):
    assert rate(client, 1, rating).json()["sm2_quality"] == quality
    assert db_session.scalar(select(ReviewLog.sm2_quality)) == quality


def test_dont_know_keeps_ease_factor_and_resets_repetitions(client, db_session):
    rate(client, 1, "dont_know")
    saved = db_session.get(UserWord, (1, 1))
    assert (saved.repetitions, saved.interval_days, saved.ease_factor) == (0, 1, Decimal("2.50"))


# ---------- 오류 ----------


def test_duplicate_rating_returns_409_and_changes_nothing(client, db_session):
    assert rate(client, 1, "know").status_code == 200
    response = rate(client, 1, "dont_know")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WORD_ALREADY_LEARNED"
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 1  # 기록이 늘지 않음
    assert db_session.get(UserWord, (1, 1)).ease_factor == Decimal("2.60")  # 첫 평가 결과 유지


def test_unknown_word_returns_404(client):
    response = rate(client, 99999)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORD_NOT_FOUND"


def test_word_beyond_free_plan_is_rejected(client, db_session):
    response = rate(client, FREE_LIMIT + 1)  # 순위 251
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PLAN_LIMIT_EXCEEDED"
    assert db_session.scalar(select(func.count()).select_from(UserWord)) == 0
    assert rate(client, FREE_LIMIT).status_code == 200  # 250 은 무료 범위


def test_word_beyond_free_plan_is_allowed_for_premium(client, db_session):
    make_premium(db_session)
    assert rate(client, FREE_LIMIT + 1).status_code == 200


@pytest.mark.parametrize("body", [{"word_id": 1, "rating": "maybe"}, {"word_id": 1}, {"rating": "know"},
                                  {"word_id": "1", "rating": "know"}, {"word_id": 0, "rating": "know"}])
def test_flashcard_validation(client, body):
    assert client.post("/api/study/flashcard", json=body).status_code == 422


def test_daily_limit_is_a_goal_not_a_block(client):
    """하루 새 단어 수는 목표치라서, 목표를 넘겨 직접 평가 요청을 보내도 막지 않는다 (인터페이스 정의서 4.3)."""
    client.patch("/api/me/settings", json={"daily_new_limit": 1})
    assert rate(client, 1).status_code == 200
    assert rate(client, 2).status_code == 200


# ---------- 요금제 범위: 새 단어 목록과 오늘 할 것 ----------


def test_free_user_who_finished_free_range_is_locked(client, db_session):
    # Given 무료 단어 250개를 모두 학습한 상태 (직접 채워 넣는다)
    now = now_utc()
    db_session.add_all(
        UserWord(user_id=1, word_id=rank, repetitions=1, interval_days=1, ease_factor=Decimal("2.50"),
                 next_review_date=now.date() + timedelta(days=1), first_learned_at=now - timedelta(days=3), last_reviewed_at=now)
        for rank in range(1, FREE_LIMIT + 1)
    )
    db_session.commit()
    # Then 새 단어는 0개, 요금제 때문에 막힘
    today = client.get("/api/study/today").json()
    assert today["new_target_count"] == 0
    assert today["new_locked_by_plan"] is True
    assert client.get("/api/study/new").json()["items"] == []
    # When 프리미엄이 되면 막힘이 풀리고 251번부터 나온다
    make_premium(db_session)
    today = client.get("/api/study/today").json()
    assert today["new_locked_by_plan"] is False
    assert today["plan_word_limit"] == WORD_COUNT
    assert client.get("/api/study/new?limit=1").json()["items"][0]["frequency_rank"] == FREE_LIMIT + 1


def test_new_words_never_exceed_free_range(client, db_session):
    now = now_utc()
    db_session.add_all(
        UserWord(user_id=1, word_id=rank, repetitions=1, interval_days=1, ease_factor=Decimal("2.50"),
                 next_review_date=now.date(), first_learned_at=now - timedelta(days=3), last_reviewed_at=now)
        for rank in range(1, FREE_LIMIT - 2)  # 1~247 학습, 248~250 남음
    )
    db_session.commit()
    ranks = [item["frequency_rank"] for item in client.get("/api/study/new").json()["items"]]
    assert ranks == [248, 249, 250]


# ---------- 설정 ----------


def test_daily_limit_setting_is_reflected_in_today_and_new(client):
    response = client.patch("/api/me/settings", json={"daily_new_limit": 3})
    assert response.status_code == 200
    assert response.json()["user"]["daily_new_limit"] == 3
    assert client.get("/api/auth/me").json()["user"]["daily_new_limit"] == 3
    today = client.get("/api/study/today").json()
    assert (today["daily_new_limit"], today["new_target_count"]) == (3, 3)
    assert len(client.get("/api/study/new").json()["items"]) == 3
    # 3개를 배우면 오늘 목표 달성
    for word in client.get("/api/study/new").json()["items"]:
        rate(client, word["word_id"])
    assert client.get("/api/study/today").json()["new_target_count"] == 0


def test_raising_limit_after_learning_adds_the_difference(client):
    for word_id in (1, 2, 3):
        rate(client, word_id)
    client.patch("/api/me/settings", json={"daily_new_limit": 5})
    today = client.get("/api/study/today").json()
    assert (today["new_learned_today"], today["new_target_count"]) == (3, 2)


@pytest.mark.parametrize("bad_value", [0, 51, -1, "15", 15.5, True, None])
def test_daily_limit_validation(client, bad_value):
    assert client.patch("/api/me/settings", json={"daily_new_limit": bad_value}).status_code == 422


@pytest.mark.parametrize("good_value", [1, 50])
def test_daily_limit_boundaries(client, good_value):
    assert client.patch("/api/me/settings", json={"daily_new_limit": good_value}).status_code == 200


# ---------- 회원 간 분리 ----------


def test_other_users_progress_is_separate(client, db_session):
    rate(client, 1)
    client.post("/api/auth/logout")
    client.post("/api/auth/signup", json={"email": "other@gmail.com", "password": "abcd1234", **SIGNUP_CONSENT})
    items = client.get("/api/study/new?limit=1").json()["items"]
    assert items[0]["frequency_rank"] == 1  # 다른 회원에게는 1번이 여전히 새 단어
