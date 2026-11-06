# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 학습 기록 요약 응답 양식 (인터페이스 정의서 4.5, FR-PROG-02~05)
# 파일 위치: src/backend/app/schemas/progress.py
from datetime import date

from pydantic import BaseModel


class TodayProgress(BaseModel):
    date: date
    reviewed_count: int  # 오늘 기록이 있는 서로 다른 단어 수 (새 단어 평가 포함)
    new_learned_count: int  # 오늘 처음 배운 새 단어 수


class MasteryCounts(BaseModel):
    new_count: int
    learning_count: int
    familiar_count: int


class ProgressSummaryResponse(BaseModel):
    today: TodayProgress
    total_learned_count: int
    total_word_count: int
    current_streak_days: int
    mastery: MasteryCounts


class LearnedWordItem(BaseModel):
    """배운 단어 목록의 한 줄 (인터페이스 정의서 4.5 확장, 이슈 #20)"""

    word_id: int
    headword: str
    part_of_speech: str
    meaning_ko: str
    example_en: str
    example_ko: str
    mastery: str  # "learning"(학습 중) / "familiar"(익숙함)
    first_learned_date: date  # 처음 배운 날 (한국 날짜)


class LearnedWordsResponse(BaseModel):
    total_count: int
    items: list[LearnedWordItem]
