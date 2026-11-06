# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - AI 선생님 API 통합 테스트 (FR-AI-02~06, NFR-AI-01~03, 이슈 #16). 가짜 담당자만 쓰고 외부 호출은 하지 않는다
# 파일 위치: src/backend/tests/test_ai_teacher.py
import logging
from datetime import timedelta

import pytest
from sqlalchemy import select

from consent_helpers import SIGNUP_CONSENT
from app.ai.fake_provider import FakeTeacherProvider
from app.ai.provider import get_teacher_provider
from app.core.config import get_settings
from app.core.timeutil import now_utc, today_kst
from app.models.ai_usage import AiUsage
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}


@pytest.fixture
def words(db_session):
    """순위 1~20 의 가짜 단어 + 무료 범위(250) 밖인 순위 300 단어(far)."""
    db_session.add_all(
        Word(headword=f"word{rank:03d}", part_of_speech="n.", meaning_ko=f"뜻{rank}", example_en=f"I see word{rank:03d}.",
             example_ko=f"나는 {rank}를 본다.", frequency_rank=rank)
        for rank in range(1, 21)
    )
    db_session.add(Word(headword="faraway", part_of_speech="adj.", meaning_ko="먼", example_en="It is faraway.",
                        example_ko="멀다.", frequency_rank=300))
    db_session.commit()


@pytest.fixture
def fake(api_client):
    """담당자를 가짜로 바꿔 끼운다(api_client 가 끝나면 자동으로 원상 복구)."""
    from app.main import app

    provider = FakeTeacherProvider()
    app.dependency_overrides[get_teacher_provider] = lambda: provider
    return provider


@pytest.fixture
def client(api_client, words, fake):
    assert api_client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    return api_client


def ask(client, word_id=1, kind="simple", context="study", question=None):
    body = {"word_id": word_id, "kind": kind, "context": context}
    if question is not None:
        body["question"] = question
    return client.post("/api/ai/teacher", json=body)


def make_premium(db_session):
    user = db_session.scalars(select(User)).one()
    user.premium_until = now_utc() + timedelta(days=10)
    db_session.commit()


def usage_count(db_session):
    db_session.expire_all()
    row = db_session.scalars(select(AiUsage)).first()
    return row.call_count if row else 0


def test_requires_login(api_client, words, fake):
    assert ask(api_client).status_code == 401
    assert fake.calls == []


def test_quick_button_returns_answer_and_remaining(client, fake):
    response = ask(client, word_id=1, kind="compare")
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("[가짜 선생님]")
    assert (body["remaining_today"], body["daily_limit"]) == (9, 10)
    system_instruction, message = fake.calls[0]
    assert "word001" in message and "뜻1" in message and "I see word001." in message
    assert "영어 단어에 대한 질문만" in system_instruction  # 주제 이탈 거절 규칙이 지시문에 있다 (FR-AI-08)


def test_only_word_info_is_sent_not_personal_data(client, fake):
    """외부로 나가는 글에 이메일·비밀번호가 없다 (NFR-AI-02)."""
    ask(client, kind="ask", question="이 단어 어떻게 외워요?")
    sent = "\n".join(system + user for system, user in fake.calls)
    assert CREDENTIALS["email"] not in sent and CREDENTIALS["password"] not in sent


def test_free_question_is_included_and_quick_button_ignores_question(client, fake):
    ask(client, kind="ask", question="이 단어 어떻게 외워요?")
    assert "이 단어 어떻게 외워요?" in fake.calls[0][1]
    ask(client, kind="simple", question="무시될 글")
    assert "무시될 글" not in fake.calls[1][1]


@pytest.mark.parametrize("question", [None, "", "   ", "가" * 201])
def test_ask_requires_valid_question(client, fake, question):
    response = ask(client, kind="ask", question=question)
    assert response.status_code == 422
    assert fake.calls == []


def test_unknown_kind_or_context_rejected(client):
    assert client.post("/api/ai/teacher", json={"word_id": 1, "kind": "hack", "context": "study"}).status_code == 422
    assert client.post("/api/ai/teacher", json={"word_id": 1, "kind": "simple", "context": "home"}).status_code == 422


def test_free_user_limit_is_10_per_day(client, fake):
    for _ in range(10):
        assert ask(client).status_code == 200
    blocked = ask(client)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "AI_LIMIT_REACHED"
    assert len(fake.calls) == 10  # 한도 초과 요청은 담당자까지 가지 않는다


def test_premium_user_gets_higher_limit(client, db_session):
    make_premium(db_session)
    body = ask(client).json()
    assert (body["remaining_today"], body["daily_limit"]) == (49, 50)


def test_limit_resets_next_day(client, db_session, monkeypatch):
    for _ in range(10):
        ask(client)
    assert ask(client).status_code == 429
    monkeypatch.setattr("app.services.ai_service.today_kst", lambda: today_kst() + timedelta(days=1))
    assert ask(client).status_code == 200


def test_failed_call_is_not_counted(client, db_session, fake):
    fake.fail = True
    response = ask(client)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert usage_count(db_session) == 0  # 미리 차감한 횟수가 돌아와 있다
    fake.fail = False
    assert ask(client).json()["remaining_today"] == 9


def test_disabled_returns_503_without_calling_provider(client, fake, monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_teacher_enabled", False)
    response = ask(client)
    assert response.status_code == 503
    assert fake.calls == []


def test_unknown_word_404(client):
    assert ask(client, word_id=9999).status_code == 404


def test_study_context_respects_plan_range(client, db_session, fake):
    far_word_id = db_session.scalars(select(Word.id).where(Word.headword == "faraway")).one()
    blocked = ask(client, word_id=far_word_id)
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "WORD_NOT_AVAILABLE"
    assert fake.calls == [] and usage_count(db_session) == 0  # 막힌 요청은 횟수도 쓰지 않는다
    make_premium(db_session)
    assert ask(client, word_id=far_word_id).status_code == 200


def test_quiz_context_requires_learned_word(client, db_session):
    blocked = ask(client, word_id=2, context="quiz")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "WORD_NOT_LEARNED"
    now = now_utc()
    db_session.add(UserWord(user_id=1, word_id=2, repetitions=1, interval_days=1, next_review_date=today_kst(),
                            first_learned_at=now, last_reviewed_at=now))
    db_session.commit()
    assert ask(client, word_id=2, context="quiz").status_code == 200


def test_logs_contain_no_question_text_or_key(client, caplog, monkeypatch):
    """질문 원문과 API 키가 로그에 남지 않는다 (NFR-AI-01)."""
    monkeypatch.setattr(get_settings(), "gemini_api_key", "AIza-secret-marker-999")
    caplog.set_level(logging.INFO)
    ask(client, kind="ask", question="비밀질문마커-4242")
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "비밀질문마커-4242" not in text
    assert "AIza-secret-marker-999" not in text
