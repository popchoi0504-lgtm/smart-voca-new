# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 학습 기록 요약 API 통합 테스트 (FR-PROG-01~05, 구현 계획서 VS-6)
# 파일 위치: src/backend/tests/test_progress.py
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from consent_helpers import SIGNUP_CONSENT
from app.core.timeutil import KST, now_utc
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}
OTHER_CREDENTIALS = {"email": "other@gmail.com", "password": "abcd1234"}
WORD_COUNT = 30

# 테스트가 보는 "지금": 한국 시간 2026-11-05 12:00 (UTC 03:00). 날짜가 갈리는 자정과 멀어 흔들리지 않는다.
NOON_KST = datetime(2026, 11, 5, 3, 0, 0, tzinfo=timezone.utc)
TODAY = date(2026, 11, 5)


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


@pytest.fixture
def now(monkeypatch):
    """요약 서비스가 보는 "지금"을 고정/이동하는 장치. now.set(datetime) 으로 바꾼다."""

    class FixedNow:
        value = NOON_KST

        def set(self, moment):
            self.value = moment

    fixed = FixedNow()
    monkeypatch.setattr("app.services.progress_service.now_utc", lambda: fixed.value)
    return fixed


def user_id_of(db_session, email="student@gmail.com"):
    return db_session.scalar(select(User.id).where(User.email == email))


def add_log(db_session, user_id, word_id, study_date, activity="quiz", result="correct"):
    db_session.add(ReviewLog(
        user_id=user_id, word_id=word_id, activity_type=activity, result=result, max_hint_level=0,
        sm2_quality=5, reviewed_at=now_utc(), study_date=study_date,
    ))
    db_session.commit()


def add_user_word(db_session, user_id, word_id, interval_days):
    db_session.add(UserWord(
        user_id=user_id, word_id=word_id, repetitions=1, interval_days=interval_days, ease_factor=2.5,
        next_review_date=TODAY, first_learned_at=now_utc(), last_reviewed_at=now_utc(),
    ))
    db_session.commit()


def summary(client):
    response = client.get("/api/progress/summary")
    assert response.status_code == 200
    return response.json()


# ---------- 로그인 필요 ----------


def test_requires_login(api_client):
    assert api_client.get("/api/progress/summary").status_code == 401


# ---------- 기본 모양 ----------


def test_empty_user_shows_zeros(client, now):
    data = summary(client)
    assert data == {
        "today": {"date": "2026-11-05", "reviewed_count": 0, "new_learned_count": 0},
        "total_learned_count": 0,
        "total_word_count": WORD_COUNT,
        "current_streak_days": 0,
        "mastery": {"new_count": WORD_COUNT, "learning_count": 0, "familiar_count": 0},
    }


def test_real_flashcards_show_up_in_summary(client, db_session):
    """실제 API 로 새 단어 3개를 배우면(시계는 진짜 지금) 오늘 3개·누적 3개·연속 1일."""
    for word_id in (1, 2, 3):
        assert client.post("/api/study/flashcard", json={"word_id": word_id, "rating": "know"}).status_code == 200
    data = summary(client)
    assert data["today"]["reviewed_count"] == 3
    assert data["today"]["new_learned_count"] == 3
    assert data["total_learned_count"] == 3
    assert data["current_streak_days"] == 1
    assert data["mastery"] == {"new_count": WORD_COUNT - 3, "learning_count": 3, "familiar_count": 0}


# ---------- 오늘 학습량 ----------


def test_reviewed_counts_distinct_words_and_new_learned_counts_only_flashcards(client, db_session, now):
    uid = user_id_of(db_session)
    add_user_word(db_session, uid, 1, 1)
    add_log(db_session, uid, 1, TODAY, "flashcard", "know")  # 새 단어로 처음 배움
    add_log(db_session, uid, 1, TODAY, "quiz", "correct")  # 같은 단어를 퀴즈로 또 풀어도 단어 수는 1
    add_user_word(db_session, uid, 2, 6)
    add_log(db_session, uid, 2, TODAY, "quiz", "wrong")  # 퀴즈만 푼 단어: 복습 1, 새 단어는 아님
    data = summary(client)
    assert data["today"]["reviewed_count"] == 2
    assert data["today"]["new_learned_count"] == 1


def test_yesterdays_logs_do_not_count_as_today(client, db_session, now):
    uid = user_id_of(db_session)
    add_user_word(db_session, uid, 1, 1)
    add_log(db_session, uid, 1, TODAY - timedelta(days=1), "flashcard", "know")
    data = summary(client)
    assert data["today"]["reviewed_count"] == 0
    assert data["today"]["new_learned_count"] == 0
    assert data["total_learned_count"] == 1  # 누적은 날짜와 상관없다


# ---------- 숙련도 구간 ----------


def test_mastery_boundary_at_21_days(client, db_session, now):
    uid = user_id_of(db_session)
    for word_id, interval in ((1, 0), (2, 20), (3, 21), (4, 22)):
        add_user_word(db_session, uid, word_id, interval)
    mastery = summary(client)["mastery"]
    assert mastery == {"new_count": WORD_COUNT - 4, "learning_count": 2, "familiar_count": 2}


def test_three_groups_always_add_up_to_total(client, db_session, now):
    uid = user_id_of(db_session)
    for word_id, interval in ((1, 1), (2, 30), (3, 6)):
        add_user_word(db_session, uid, word_id, interval)
    data = summary(client)
    mastery = data["mastery"]
    assert mastery["new_count"] + mastery["learning_count"] + mastery["familiar_count"] == data["total_word_count"]


# ---------- 연속 학습일 ----------


def test_streak_before_studying_today_keeps_yesterday(client, db_session, now):
    uid = user_id_of(db_session)
    for ago in (1, 2, 3):
        add_log(db_session, uid, 1, TODAY - timedelta(days=ago))
    data = summary(client)
    assert data["today"]["reviewed_count"] == 0
    assert data["current_streak_days"] == 3


def test_streak_includes_today(client, db_session, now):
    uid = user_id_of(db_session)
    for ago in (0, 1, 2):
        add_log(db_session, uid, 1, TODAY - timedelta(days=ago))
    assert summary(client)["current_streak_days"] == 3


def test_streak_resets_after_skipping_a_day(client, db_session, now):
    uid = user_id_of(db_session)
    for ago in (2, 3, 4):
        add_log(db_session, uid, 1, TODAY - timedelta(days=ago))
    assert summary(client)["current_streak_days"] == 0


def test_streak_counts_only_the_latest_run(client, db_session, now):
    uid = user_id_of(db_session)
    for ago in (0, 1, 3, 4, 5, 6):
        add_log(db_session, uid, 1, TODAY - timedelta(days=ago))
    assert summary(client)["current_streak_days"] == 2


def test_many_logs_on_one_day_count_as_one_day(client, db_session, now):
    uid = user_id_of(db_session)
    for word_id in (1, 2, 3, 4):
        add_log(db_session, uid, word_id, TODAY)
    assert summary(client)["current_streak_days"] == 1


def test_streak_with_clock_moving_from_real_study(client, db_session, now):
    """실제 API 로 배운 날을 기준으로, 시계를 하루씩 옮기면: 같은 날 1 → 다음 날(아직 안 함) 1 → 이틀 뒤 0."""
    # 서비스(study)는 진짜 지금으로 기록하므로, 요약 쪽 "지금"도 진짜 지금에서 시작한다
    now.set(now_utc())
    assert client.post("/api/study/flashcard", json={"word_id": 1, "rating": "know"}).status_code == 200
    assert summary(client)["current_streak_days"] == 1
    now.set(now_utc() + timedelta(days=1))
    data = summary(client)
    assert data["current_streak_days"] == 1  # 다음 날 아직 학습 전: 끊기지 않음
    assert data["today"]["reviewed_count"] == 0
    now.set(now_utc() + timedelta(days=2))
    assert summary(client)["current_streak_days"] == 0


# ---------- 한국 시간 기준 날짜 ----------


def test_day_changes_at_midnight_kst_not_utc(client, db_session, now):
    """11-05 한국 자정 직전(UTC 14:59:59)은 11-05, 자정(UTC 15:00:00)은 11-06."""
    uid = user_id_of(db_session)
    add_log(db_session, uid, 1, date(2026, 11, 5))
    now.set(datetime(2026, 11, 5, 14, 59, 59, tzinfo=timezone.utc))
    data = summary(client)
    assert data["today"]["date"] == "2026-11-05"
    assert data["today"]["reviewed_count"] == 1
    assert data["current_streak_days"] == 1
    now.set(datetime(2026, 11, 5, 15, 0, 0, tzinfo=timezone.utc))
    data = summary(client)
    assert data["today"]["date"] == "2026-11-06"
    assert data["today"]["reviewed_count"] == 0  # 날짜가 바뀌어 오늘 학습량은 0
    assert data["current_streak_days"] == 1  # 어제(11-05) 기록으로 아직 이어진다


def test_utc_morning_before_9am_kst_is_still_same_kst_day(client, db_session, now):
    """한국 11-06 오전 8시 = UTC 11-05 23:00. UTC 날짜(11-05)가 아니라 한국 날짜(11-06)를 쓴다."""
    uid = user_id_of(db_session)
    add_log(db_session, uid, 1, date(2026, 11, 6))
    now.set(datetime(2026, 11, 5, 23, 0, 0, tzinfo=timezone.utc))
    data = summary(client)
    assert data["today"]["date"] == "2026-11-06"
    assert data["today"]["reviewed_count"] == 1
    assert now.value.astimezone(KST).date() == date(2026, 11, 6)


# ---------- 다른 회원의 기록 ----------


def test_other_users_records_are_not_mixed_in(client, db_session, now):
    assert client.post("/api/auth/signup", json={**OTHER_CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201  # 쿠키가 other 로 바뀐다
    other_id = user_id_of(db_session, "other@gmail.com")
    for ago in (0, 1, 2, 3):
        add_log(db_session, other_id, 1, TODAY - timedelta(days=ago))
    add_user_word(db_session, other_id, 1, 30)
    assert client.post("/api/auth/login", json=CREDENTIALS).status_code == 200  # 다시 student 로 본다
    data = summary(client)
    assert data["current_streak_days"] == 0
    assert data["total_learned_count"] == 0
    assert data["today"]["reviewed_count"] == 0
