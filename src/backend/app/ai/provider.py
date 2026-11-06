# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - AI 선생님 담당자(provider)의 공통 모양과 선택 함수 (FR-AI-06, NFR-AI-03)
# 파일 위치: src/backend/app/ai/provider.py
# 서비스 로직은 "질문을 보내고 답을 받는다"만 알고, 담당자가 Gemini 인지 가짜인지는 모른다 → 결제 담당자와 같은 방식.
from typing import Protocol

from app.core.config import get_settings
from app.core.errors import AppError


class AiUnavailable(Exception):
    """AI 답변을 받지 못했다(꺼짐, 설정 오류, 통신 실패, 시간 초과, 안전 필터 차단, 빈 응답). 사용자에게는 같은 안내를 보여 준다."""


class TeacherProvider(Protocol):
    """AI 담당자가 지켜야 할 모양. ask 하나뿐이다."""

    name: str

    def ask(self, system_instruction: str, user_message: str) -> str:
        """시스템 지시문과 질문을 보내 답(글)을 받는다. 실패하면 AiUnavailable."""
        ...


def get_teacher_provider() -> TeacherProvider:
    """설정(AI_PROVIDER)에 따라 담당자를 고른다. FastAPI 의존성으로 쓰며, 테스트는 이 함수를 바꿔 끼운다."""
    settings = get_settings()
    if settings.ai_provider == "gemini":
        from app.ai.gemini_provider import GeminiTeacherProvider

        try:
            return GeminiTeacherProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        except AiUnavailable as error:
            # 키·모델 설정이 비어 있는 경우도 사용자에게는 같은 모양의 503 으로 보여 준다
            raise AppError(503, "AI_UNAVAILABLE", "지금은 AI 선생님이 답할 수 없어요. 잠시 후 다시 물어봐 주세요.") from error
    from app.ai.fake_provider import FakeTeacherProvider

    return FakeTeacherProvider()
