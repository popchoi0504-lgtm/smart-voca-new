# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 학습(오늘 할 것, 새 단어, 플래시카드)과 설정의 요청/응답 양식 (인터페이스 정의서 4.2·4.3)
# 파일 위치: src/backend/app/schemas/study.py
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, StrictInt

from app.schemas.auth import UserOut

DAILY_NEW_LIMIT_MIN = 1
DAILY_NEW_LIMIT_MAX = 50


class SettingsRequest(BaseModel):
    """설정 변경 요청. StrictInt: "15" 같은 문자나 true 는 받지 않고 정수만 받는다."""

    daily_new_limit: StrictInt = Field(ge=DAILY_NEW_LIMIT_MIN, le=DAILY_NEW_LIMIT_MAX)


class UserResponse(BaseModel):
    user: UserOut


class TodayResponse(BaseModel):
    today: date
    review_due_count: int
    new_target_count: int
    new_learned_today: int
    daily_new_limit: int
    plan_word_limit: int
    new_locked_by_plan: bool


class NewWordItem(BaseModel):
    """학습 카드용 단어. 공부용이라 영단어를 보낸다(퀴즈와 다름)."""

    word_id: int
    headword: str
    part_of_speech: str
    meaning_ko: str
    example_en: str
    example_ko: str
    frequency_rank: int


class NewWordsResponse(BaseModel):
    items: list[NewWordItem]


class FlashcardRequest(BaseModel):
    word_id: StrictInt = Field(ge=1)
    rating: Literal["dont_know", "unsure", "know"]


class FlashcardResponse(BaseModel):
    word_id: int
    sm2_quality: int
    interval_days: int
    next_review_date: date
