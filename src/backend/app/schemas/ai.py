# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - AI 선생님 요청/응답 양식 (AI 선생님 설계서 5장)
# 파일 위치: src/backend/app/schemas/ai.py
from typing import Literal

from pydantic import BaseModel, Field, StrictInt, model_validator

QUESTION_MAX_LENGTH = 200


class TeacherRequest(BaseModel):
    word_id: StrictInt
    kind: Literal["simple", "compare", "example", "ask"]  # 빠른 버튼 3종 + 직접 질문
    context: Literal["study", "quiz"]  # 어느 화면에서 물었는지(새 단어 / 퀴즈)
    question: str | None = Field(default=None, max_length=QUESTION_MAX_LENGTH)

    @model_validator(mode="after")
    def question_only_for_ask(self):
        if self.kind == "ask":
            if self.question is None or not self.question.strip():
                raise ValueError("질문을 입력해 주세요.")
        else:
            self.question = None  # 빠른 버튼에는 질문 글이 필요 없다. 실수로 와도 버린다
        return self


class TeacherResponse(BaseModel):
    answer: str
    remaining_today: int  # 오늘 남은 횟수
    daily_limit: int  # 내 요금제의 하루 한도
