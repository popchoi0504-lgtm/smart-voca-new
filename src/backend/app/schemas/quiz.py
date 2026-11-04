# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 퀴즈(문제 목록, 힌트, 답 제출)의 요청/응답 양식 (인터페이스 정의서 4.4)
# 파일 위치: src/backend/app/schemas/quiz.py
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, StrictInt, model_validator

ANSWER_MAX_LENGTH = 100


class QuizItem(BaseModel):
    """문제 한 개. 정답 영단어는 일부러 넣지 않았다(AD-7): 이 양식에 필드가 없어서 실수로도 나갈 수 없다."""

    word_id: int
    part_of_speech: str
    meaning_ko: str
    example_masked: str | None  # 예문의 영단어를 ______ 로 가린 것. 예문에 단어가 없으면 null
    letter_count: int


class QuizQueueResponse(BaseModel):
    items: list[QuizItem]
    remaining_due_count: int  # 오늘 복습 대상 전체 개수(이번에 내려보낸 것 포함)


class HintRequest(BaseModel):
    level: Literal[1, 2, 3]


class HintResponse(BaseModel):
    """단계마다 쓰는 필드가 다르다. 쓰지 않는 필드는 응답에서 빠진다(response_model_exclude_unset)."""

    level: int
    skipped: bool | None = None
    scrambled: str | None = None
    masked: list[str] | None = None
    answer: str | None = None


class AnswerRequest(BaseModel):
    answer: str | None = Field(default=None, max_length=ANSWER_MAX_LENGTH)
    max_hint_level: StrictInt = Field(ge=0, le=3)

    @model_validator(mode="after")
    def answer_needed_unless_revealed(self):
        # 정답 확인(3단계)이면 입력 없이 제출할 수 있다. 그 밖에는 답을 입력해야 한다
        if self.max_hint_level < 3 and (self.answer is None or not self.answer.strip()):
            raise ValueError("정답을 입력해 주세요.")
        return self


class AnswerResponse(BaseModel):
    result: Literal["correct", "wrong", "revealed"]
    recorded: bool
    practice: bool
    sm2_quality: int | None
    interval_days: int | None
    next_review_date: date | None
    correct_answer: str | None  # 정답·정답 확인일 때만. 오답이면 null
    remaining_due_count: int
