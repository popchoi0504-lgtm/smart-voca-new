# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - Gemini API 호출 담당자 (FR-AI-02, NFR-AI-01·04)
# 파일 위치: src/backend/app/ai/gemini_provider.py
# 근거: 공식 문서(2026-11-06 확인) POST https://generativelanguage.googleapis.com/v1beta/models/{모델}:generateContent, 키는 x-goog-api-key 헤더.
# 모델 이름은 문서마다 달라서 코드에 쓰지 않고 GEMINI_MODEL 로 받는다. 키·질문 원문은 로그에 남기지 않는다.
import logging

import httpx

from app.ai.provider import AiUnavailable

logger = logging.getLogger("smart_voca.ai")

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
TIMEOUT_SECONDS = 15.0  # NFR-AI-04
MAX_OUTPUT_TOKENS = 1024
MAX_ANSWER_CHARS = 1500  # 화면에 보여 줄 답의 최대 길이(넘으면 자른다)


class GeminiTeacherProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key or not model:
            raise AiUnavailable("GEMINI_API_KEY 또는 GEMINI_MODEL 이 설정되지 않았습니다.")
        self._url = f"{BASE_URL}/{model}:generateContent"
        self._api_key = api_key

    def ask(self, system_instruction: str, user_message: str) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": MAX_OUTPUT_TOKENS},
        }
        try:
            response = httpx.post(
                self._url, json=body, headers={"x-goog-api-key": self._api_key}, timeout=TIMEOUT_SECONDS
            )
        except httpx.HTTPError as error:
            raise AiUnavailable("Gemini 통신 실패") from error

        if response.status_code != 200:
            # 본문에는 요청 내용이 섞일 수 있어 상태 코드만 남긴다
            logger.warning("Gemini 오류 응답 status=%s", response.status_code)
            raise AiUnavailable(f"Gemini 오류 응답 {response.status_code}")
        return _extract_answer(response)


def _extract_answer(response: httpx.Response) -> str:
    """응답에서 답 글만 꺼낸다. 차단되었거나 비어 있으면 AiUnavailable."""
    try:
        data = response.json()
    except ValueError as error:
        raise AiUnavailable("Gemini 응답을 읽을 수 없음") from error
    if not isinstance(data, dict):
        raise AiUnavailable("Gemini 응답 모양이 예상과 다름")
    if (data.get("promptFeedback") or {}).get("blockReason"):
        raise AiUnavailable("Gemini 가 요청을 차단함")
    candidates = data.get("candidates") or []
    if not candidates:
        raise AiUnavailable("Gemini 응답에 후보가 없음")
    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise AiUnavailable("Gemini 응답이 비어 있음")
    return text[:MAX_ANSWER_CHARS]
