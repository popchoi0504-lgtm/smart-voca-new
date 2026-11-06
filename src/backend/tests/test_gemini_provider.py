# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - Gemini 담당자 단위 테스트: 가짜 HTTP 응답으로 정상·차단·빈 응답·오류·시간 초과를 확인 (이슈 #16). 외부 호출 없음
# 파일 위치: src/backend/tests/test_gemini_provider.py
import httpx
import pytest

from app.ai.gemini_provider import MAX_ANSWER_CHARS, GeminiTeacherProvider
from app.ai.provider import AiUnavailable

KEY = "AIza-test-key-123"


def ok_response(text="안녕하세요"):
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]})


@pytest.fixture
def provider():
    return GeminiTeacherProvider(api_key=KEY, model="test-model")


def patch_post(monkeypatch, response=None, error=None):
    sent = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        sent.update(url=url, body=json, headers=headers, timeout=timeout)
        if error:
            raise error
        return response

    monkeypatch.setattr("app.ai.gemini_provider.httpx.post", fake_post)
    return sent


def test_request_shape_and_answer(provider, monkeypatch):
    sent = patch_post(monkeypatch, ok_response("설명입니다"))
    assert provider.ask("규칙", "질문") == "설명입니다"
    assert sent["url"].endswith("/models/test-model:generateContent")
    assert sent["headers"] == {"x-goog-api-key": KEY}  # 키는 헤더로만 보낸다(주소에 넣지 않는다)
    assert KEY not in sent["url"]
    assert sent["body"]["systemInstruction"]["parts"][0]["text"] == "규칙"
    assert sent["body"]["contents"][0]["parts"][0]["text"] == "질문"
    assert sent["timeout"] == 15.0


def test_multiple_parts_are_joined(provider, monkeypatch):
    patch_post(monkeypatch, httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "가"}, {"text": "나"}]}}]}))
    assert provider.ask("s", "u") == "가나"


def test_long_answer_is_cut(provider, monkeypatch):
    patch_post(monkeypatch, ok_response("가" * (MAX_ANSWER_CHARS + 500)))
    assert len(provider.ask("s", "u")) == MAX_ANSWER_CHARS


@pytest.mark.parametrize("response", [
    httpx.Response(429, json={"error": {"message": "quota"}}),
    httpx.Response(500, text="oops"),
    httpx.Response(200, text="not json"),
    httpx.Response(200, json=[1, 2]),
    httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}}),
    httpx.Response(200, json={"candidates": []}),
    httpx.Response(200, json={"candidates": [{"content": {"parts": []}}]}),
    httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "   "}]}}]}),
])
def test_bad_responses_become_unavailable(provider, monkeypatch, response):
    patch_post(monkeypatch, response)
    with pytest.raises(AiUnavailable):
        provider.ask("s", "u")


@pytest.mark.parametrize("error", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
def test_network_errors_become_unavailable(provider, monkeypatch, error):
    patch_post(monkeypatch, error=error)
    with pytest.raises(AiUnavailable):
        provider.ask("s", "u")


@pytest.mark.parametrize("api_key, model", [("", "m"), (KEY, ""), ("", "")])
def test_missing_settings_are_unavailable(api_key, model):
    with pytest.raises(AiUnavailable):
        GeminiTeacherProvider(api_key=api_key, model=model)


def test_error_log_has_status_only(provider, monkeypatch, caplog):
    patch_post(monkeypatch, httpx.Response(400, text=f"bad request echo {KEY} 질문원문"))
    with pytest.raises(AiUnavailable):
        provider.ask("s", "질문원문")
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert KEY not in text and "질문원문" not in text
