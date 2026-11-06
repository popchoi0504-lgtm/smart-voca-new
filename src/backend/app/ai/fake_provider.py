# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 가짜 AI 담당자: 외부 호출 없이 고정 모양의 답을 돌려준다 (테스트·개발·시연 대비용)
# 파일 위치: src/backend/app/ai/fake_provider.py
from app.ai.provider import AiUnavailable


class FakeTeacherProvider:
    name = "fake"

    def __init__(self, fail: bool = False):
        self.fail = fail  # 테스트에서 "담당자 실패" 상황을 만들 때 쓴다
        self.calls: list[tuple[str, str]] = []  # 받은 (시스템 지시문, 질문) 기록. 테스트가 무엇이 보내졌는지 확인한다

    def ask(self, system_instruction: str, user_message: str) -> str:
        self.calls.append((system_instruction, user_message))
        if self.fail:
            raise AiUnavailable("가짜 담당자 실패")
        first_line = user_message.splitlines()[0] if user_message else ""
        return f"[가짜 선생님] {first_line} 에 대한 설명이에요. (개발용 답변입니다)"
