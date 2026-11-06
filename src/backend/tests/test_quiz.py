# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 퀴즈 문제 목록·힌트·답 제출 API 통합 테스트 (FR-QUIZ-01~03, FR-HINT-01~05, FR-SRS-02~05, IF-4·IF-5, VS-4)
# 파일 위치: src/backend/tests/test_quiz.py
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from consent_helpers import SIGNUP_CONSENT
from app.core.timeutil import KST, now_utc
from app.models.review_log import ReviewLog
from app.models.user_word import UserWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}


@pytest.fixture
def words(db_session):
    """순위 1~20 의 가짜 단어. 영단어는 word001 처럼 길이 7, 예문은 'I see word001.'"""
    db_session.add_all(
        Word(headword=f"word{rank:03d}", part_of_speech="n.", meaning_ko=f"뜻{rank}", example_en=f"I see word{rank:03d}.",
             example_ko=f"나는 {rank}를 본다.", frequency_rank=rank)
        for rank in range(1, 21)
    )
    db_session.commit()


@pytest.fixture
def client(api_client, words):
    assert api_client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    return api_client


@pytest.fixture
def clock(monkeypatch):
    """퀴즈·학습 서비스가 보는 "지금"을 함께 옮긴다."""

    class Clock:
        offset = timedelta(0)

        def advance(self, **kwargs):
            self.offset += timedelta(**kwargs)

    fake = Clock()
    for module in ("study_service", "quiz_service"):
        monkeypatch.setattr(f"app.services.{module}.now_utc", lambda: now_utc() + fake.offset)
    return fake


def today_kst():
    return now_utc().astimezone(KST).date()


def learn(db_session, word_id, due_in_days=0, interval_days=1, repetitions=1):
    """user_words 행을 직접 만든다. due_in_days=0 이면 오늘 복습 대상, 음수면 밀린 단어, 양수면 아직 아님."""
    now = now_utc()
    db_session.add(UserWord(
        user_id=1, word_id=word_id, repetitions=repetitions, interval_days=interval_days,
        next_review_date=today_kst() + timedelta(days=due_in_days), first_learned_at=now, last_reviewed_at=now,
    ))
    db_session.commit()


def answer(client, word_id, text, hint_level=0):
    return client.post(f"/api/quiz/{word_id}/answer", json={"answer": text, "max_hint_level": hint_level})


def hint(client, word_id, level):
    return client.post(f"/api/quiz/{word_id}/hint", json={"level": level})


# ---------- 로그인 필요 ----------


@pytest.mark.parametrize("method,path", [("get", "/api/quiz/queue"), ("post", "/api/quiz/1/hint"), ("post", "/api/quiz/1/answer")])
def test_requires_login(api_client, method, path):
    assert getattr(api_client, method)(path).status_code == 401


# ---------- 문제 목록 ----------


def test_queue_is_empty_when_nothing_is_due(client, db_session):
    learn(db_session, 1, due_in_days=1)
    body = client.get("/api/quiz/queue").json()
    assert body == {"items": [], "remaining_due_count": 0}


def test_queue_never_contains_the_answer_word(client, db_session):
    """핵심 보안 규칙(AD-7): 문제 목록 응답 어디에도 정답 영단어가 없다."""
    for word_id in (1, 2, 3):
        learn(db_session, word_id)
    response = client.get("/api/quiz/queue")
    for word_id in (1, 2, 3):
        assert f"word{word_id:03d}" not in response.text.lower()
    item = response.json()["items"][0]
    assert set(item) == {"word_id", "part_of_speech", "meaning_ko", "example_masked", "letter_count"}
    assert item["example_masked"] == "I see ______."
    assert item["letter_count"] == 7


def test_queue_orders_most_overdue_first(client, db_session):
    learn(db_session, 5, due_in_days=-1)
    learn(db_session, 3, due_in_days=-9)
    learn(db_session, 4, due_in_days=0)
    learn(db_session, 6, due_in_days=2)  # 아직 아님
    items = client.get("/api/quiz/queue").json()["items"]
    assert [item["word_id"] for item in items] == [3, 5, 4]


def test_queue_limits_one_session_but_reports_total(client, db_session):
    for word_id in range(1, 13):
        learn(db_session, word_id)
    body = client.get("/api/quiz/queue").json()
    assert len(body["items"]) == 10
    assert body["remaining_due_count"] == 12
    assert len(client.get("/api/quiz/queue?limit=3").json()["items"]) == 3


@pytest.mark.parametrize("bad_limit", [0, 11, "abc"])
def test_queue_limit_validation(client, bad_limit):
    assert client.get(f"/api/quiz/queue?limit={bad_limit}").status_code == 422


def test_queue_example_masked_is_null_when_example_lacks_the_word(client, db_session):
    learn(db_session, 1)
    db_session.get(Word, 1).example_en = "Nothing to hide here."
    db_session.commit()
    assert client.get("/api/quiz/queue").json()["items"][0]["example_masked"] is None


def test_queue_only_shows_own_words(client, db_session, api_client):
    learn(db_session, 1)
    api_client.post("/api/auth/logout")
    api_client.post("/api/auth/signup", json={"email": "other@gmail.com", "password": "abcd1234", **SIGNUP_CONSENT})
    assert api_client.get("/api/quiz/queue").json()["items"] == []


# ---------- 힌트 ----------


def test_hint_levels_return_expected_shapes(client, db_session):
    learn(db_session, 1)
    first = hint(client, 1, 1).json()
    assert set(first) == {"level", "skipped", "scrambled"}
    assert first["skipped"] is False
    assert first["scrambled"] != "word001" and sorted(first["scrambled"]) == sorted("word001")
    second = hint(client, 1, 2).json()
    assert set(second) == {"level", "masked"}
    assert second["masked"][0] == "w" and "_" in second["masked"]
    assert all(shown in (real, "_") for shown, real in zip(second["masked"], "word001"))
    assert hint(client, 1, 3).json() == {"level": 3, "answer": "word001"}


def test_hint_level_1_skipped_for_short_word(client, db_session):
    db_session.get(Word, 1).headword = "cat"
    db_session.commit()
    learn(db_session, 1)
    assert hint(client, 1, 1).json() == {"level": 1, "skipped": True, "scrambled": None}


def test_hint_is_same_all_day_but_changes_on_other_days(client, db_session, clock):
    """IF-5: 같은 날 반복 요청으로 공개 위치를 바꿔 가며 정답을 모을 수 없다."""
    learn(db_session, 1)
    same_day = {tuple(hint(client, 1, 2).json()["masked"]) for _ in range(10)}
    assert len(same_day) == 1
    assert len({hint(client, 1, 1).json()["scrambled"] for _ in range(10)}) == 1
    other_days = set()
    for _ in range(8):
        clock.advance(days=1)
        other_days.add(tuple(hint(client, 1, 2).json()["masked"]))
    assert len(other_days | same_day) > 1


def test_hint_differs_between_users(client, db_session, api_client):
    learn(db_session, 1)
    mine = hint(client, 1, 1).json()["scrambled"]
    api_client.post("/api/auth/logout")
    api_client.post("/api/auth/signup", json={"email": "other@gmail.com", "password": "abcd1234", **SIGNUP_CONSENT})
    now = now_utc()
    db_session.add(UserWord(user_id=2, word_id=1, next_review_date=today_kst(), first_learned_at=now, last_reviewed_at=now))
    db_session.commit()
    others = {hint(api_client, 1, 1).json()["scrambled"] for _ in range(3)}
    assert len(others) == 1  # 그 사람에게도 일정
    # 회원마다 결과가 같다고 단정하진 않지만, 서로 다른 회원이 같은 값을 받을 확률은 낮다(7글자: 약 1/2520)
    assert mine not in others


def test_hint_errors(client, db_session):
    assert hint(client, 1, 1).status_code == 409  # 아직 학습하지 않음
    assert hint(client, 1, 1).json()["error"]["code"] == "WORD_NOT_LEARNED"
    assert hint(client, 999, 1).status_code == 404
    learn(db_session, 1)
    assert hint(client, 1, 4).status_code == 422
    assert hint(client, 1, 0).status_code == 422


# ---------- 답 제출 ----------


def test_correct_without_hint_records_quiz_and_moves_next_review(client, db_session):
    learn(db_session, 1, interval_days=1, repetitions=1)
    body = answer(client, 1, "word001").json()
    assert body["result"] == "correct" and body["recorded"] is True and body["practice"] is False
    assert body["sm2_quality"] == 5
    assert body["interval_days"] == 6  # 두 번째 성공 → 6일
    assert body["next_review_date"] == str(today_kst() + timedelta(days=6))
    assert body["correct_answer"] == "word001"
    assert body["remaining_due_count"] == 0
    log = db_session.scalar(select(ReviewLog))
    assert (log.activity_type, log.result, log.max_hint_level, log.sm2_quality) == ("quiz", "correct", 0, 5)
    db_session.expire_all()
    assert db_session.get(UserWord, (1, 1)).interval_days == 6


def test_answer_ignores_case_and_surrounding_spaces(client, db_session):
    learn(db_session, 1)
    assert answer(client, 1, "  WORD001 ").json()["result"] == "correct"


def test_wrong_answer_hides_correct_answer_and_records_failure(client, db_session):
    learn(db_session, 1, interval_days=6, repetitions=2)
    response = answer(client, 1, "nope")
    body = response.json()
    assert body["result"] == "wrong" and body["correct_answer"] is None
    assert "word001" not in response.text
    assert (body["sm2_quality"], body["interval_days"]) == (1, 1)  # 실패 → 내일 다시
    log = db_session.scalar(select(ReviewLog))
    assert (log.result, log.sm2_quality) == ("wrong", 1)


def test_retry_after_wrong_is_practice_and_not_counted(client, db_session):
    """FR-QUIZ-03 + IF-4: 오답 뒤 다시 시도해 정답을 맞혀도 SM-2 에는 첫 제출만 반영된다."""
    learn(db_session, 1, interval_days=6, repetitions=2)
    answer(client, 1, "nope")
    retry = answer(client, 1, "word001").json()
    assert retry["result"] == "correct"
    assert (retry["recorded"], retry["practice"]) == (False, True)
    assert retry["sm2_quality"] is None and retry["interval_days"] is None and retry["next_review_date"] is None
    assert retry["correct_answer"] == "word001"
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 1
    db_session.expire_all()
    assert db_session.get(UserWord, (1, 1)).interval_days == 1  # 첫 오답 결과 그대로


def test_same_correct_request_twice_counts_once(client, db_session):
    learn(db_session, 1, interval_days=1, repetitions=1)
    first = answer(client, 1, "word001").json()
    second = answer(client, 1, "word001").json()
    assert first["recorded"] is True and second["practice"] is True
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 1
    db_session.expire_all()
    assert db_session.get(UserWord, (1, 1)).interval_days == 6  # 두 번 곱해지지 않음


def test_not_due_word_is_practice(client, db_session):
    learn(db_session, 1, due_in_days=5, interval_days=6)
    body = answer(client, 1, "word001").json()
    assert (body["recorded"], body["practice"]) == (False, True)
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 0
    db_session.expire_all()
    assert db_session.get(UserWord, (1, 1)).interval_days == 6


@pytest.mark.parametrize("hint_level,expected_quality", [(1, 4), (2, 3)])
def test_correct_after_hint_gets_lower_quality(client, db_session, hint_level, expected_quality):
    learn(db_session, 1)
    body = answer(client, 1, "word001", hint_level).json()
    assert (body["result"], body["sm2_quality"]) == ("correct", expected_quality)
    log = db_session.scalar(select(ReviewLog))
    assert log.max_hint_level == hint_level


def test_revealed_is_recorded_separately_from_wrong(client, db_session):
    """D-5: 정답 확인(3단계)은 오답이 아니라 revealed 로 따로 기록되고, 입력이 틀려도 revealed 다."""
    learn(db_session, 1)
    learn(db_session, 2)
    no_input = answer(client, 1, None, 3).json()
    assert (no_input["result"], no_input["correct_answer"], no_input["sm2_quality"]) == ("revealed", "word001", 2)
    typed_wrong = answer(client, 2, "zzz", 3).json()
    assert typed_wrong["result"] == "revealed"
    logs = db_session.scalars(select(ReviewLog).order_by(ReviewLog.id)).all()
    assert [(log.result, log.max_hint_level, log.sm2_quality) for log in logs] == [("revealed", 3, 2)] * 2


def test_next_day_the_word_is_due_and_counts_again(client, db_session, clock):
    learn(db_session, 1, interval_days=0, repetitions=0)
    assert answer(client, 1, "word001").json()["interval_days"] == 1
    assert client.get("/api/quiz/queue").json()["items"] == []
    clock.advance(days=1)
    assert [item["word_id"] for item in client.get("/api/quiz/queue").json()["items"]] == [1]
    second = answer(client, 1, "word001").json()
    assert second["recorded"] is True and second["interval_days"] == 6
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 2


def test_remaining_due_count_decreases(client, db_session):
    learn(db_session, 1)
    learn(db_session, 2)
    assert answer(client, 1, "word001").json()["remaining_due_count"] == 1


def test_answer_errors(client, db_session):
    assert answer(client, 1, "x").status_code == 409  # 아직 학습하지 않음
    assert answer(client, 999, "x").status_code == 404
    learn(db_session, 1)
    assert answer(client, 1, None, 0).status_code == 422  # 답이 없는데 3단계도 아님
    assert answer(client, 1, "   ", 2).status_code == 422
    assert answer(client, 1, "x", 4).status_code == 422
    assert answer(client, 1, "x", -1).status_code == 422
    assert answer(client, 1, "x" * 101, 0).status_code == 422


# ---------- 확인 퀴즈: 새 단어 학습 직후 (이슈 #21) ----------


def check(client, ids):
    return client.get(f"/api/quiz/check?word_ids={ids}")


def test_check_requires_login(api_client):
    assert check(api_client, "1").status_code == 401


def test_check_returns_learned_words_in_requested_order_without_duplicates(client, db_session):
    for word_id in (1, 2, 3):
        learn(db_session, word_id, due_in_days=1)  # 갓 배운 단어: 복습일이 내일
    response = check(client, "3,1,3,2")
    assert response.status_code == 200
    assert [item["word_id"] for item in response.json()["items"]] == [3, 1, 2]


def test_check_never_contains_the_answer_word(client, db_session):
    """AD-7: 확인 퀴즈 응답에도 정답 영단어가 없다."""
    for word_id in (1, 2):
        learn(db_session, word_id, due_in_days=1)
    response = check(client, "1,2")
    assert "word001" not in response.text.lower() and "word002" not in response.text.lower()
    item = response.json()["items"][0]
    assert set(item) == {"word_id", "part_of_speech", "meaning_ko", "example_masked", "letter_count"}
    assert item["example_masked"] == "I see ______."


def test_check_accepts_ten_but_rejects_eleven(client, db_session):
    for word_id in range(1, 12):
        learn(db_session, word_id, due_in_days=1)
    assert check(client, ",".join(str(i) for i in range(1, 11))).status_code == 200
    assert check(client, ",".join(str(i) for i in range(1, 12))).status_code == 422
    assert check(client, ",".join(["1"] * 11)).status_code == 200  # 중복은 먼저 제거하므로 1개로 센다


@pytest.mark.parametrize("raw", ["", "abc", "1,,2", "1,-2", "1.5"])
def test_check_rejects_malformed_ids(client, db_session, raw):
    learn(db_session, 1, due_in_days=1)
    assert check(client, raw).status_code == 422


def test_check_rejects_unlearned_and_unknown_words(client, db_session):
    learn(db_session, 1, due_in_days=1)
    assert check(client, "1,2").status_code == 409  # 2번은 아직 배우지 않음
    assert check(client, "1,999").status_code == 404


def test_check_rejects_another_users_words(api_client, client, db_session):
    learn(db_session, 1, due_in_days=1)  # user 1 이 배움
    api_client.post("/api/auth/logout")
    api_client.post("/api/auth/signup", json={"email": "other@gmail.com", "password": "abcd1234", **SIGNUP_CONSENT})
    response = check(api_client, "1")
    assert response.status_code == 409 and response.json()["error"]["code"] == "WORD_NOT_LEARNED"


def test_check_and_practice_answers_leave_schedule_and_logs_unchanged(client, db_session):
    learn(db_session, 1, due_in_days=1, interval_days=1, repetitions=1)
    before = db_session.get(UserWord, (1, 1))
    snapshot = (before.repetitions, before.interval_days, before.ease_factor, before.next_review_date)
    db_session.expire_all()
    assert check(client, "1").status_code == 200
    for text in ("wrong", "word001"):  # 틀린 답, 맞는 답 모두 연습
        body = answer(client, 1, text).json()
        assert body["practice"] is True and body["recorded"] is False
    db_session.expire_all()
    after = db_session.get(UserWord, (1, 1))
    assert (after.repetitions, after.interval_days, after.ease_factor, after.next_review_date) == snapshot
    assert db_session.scalar(select(func.count()).select_from(ReviewLog)) == 0
