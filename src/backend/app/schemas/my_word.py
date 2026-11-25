# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 내 단어(등록·목록·CSV·공부)의 요청/응답 양식 (이슈 #24)
# 파일 위치: src/backend/app/schemas/my_word.py
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

HEADWORD_MAX_LENGTH = 100
MEANING_MAX_LENGTH = 200
CSV_TEXT_MAX_LENGTH = 1_000_000  # 약 1MB. 제공 CSV(2,000행)는 약 60KB 라 넉넉하다


def _strip_required(value: str, label: str) -> str:
    """앞뒤 공백을 지우고, 비어 있으면 오류. 줄바꿈이 섞여 있으면 한 칸 값이 아니므로 거절한다."""
    value = value.strip()
    if not value:
        raise ValueError(f"{label}을(를) 입력해 주세요.")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{label}에는 줄바꿈을 쓸 수 없어요.")
    return value


class MyWordRequest(BaseModel):
    """등록·수정 공통 입력."""

    headword: str = Field(max_length=HEADWORD_MAX_LENGTH)
    meaning_ko: str = Field(max_length=MEANING_MAX_LENGTH)

    @field_validator("headword")
    @classmethod
    def _check_headword(cls, value: str) -> str:
        return _strip_required(value, "영단어")

    @field_validator("meaning_ko")
    @classmethod
    def _check_meaning(cls, value: str) -> str:
        return _strip_required(value, "뜻")


class MyWordOut(BaseModel):
    id: int
    headword: str
    meaning_ko: str
    next_review_date: date
    created_date: date  # 등록한 날 (한국 날짜)


class MyWordListResponse(BaseModel):
    total_count: int  # 검색 조건에 맞는 전체 개수
    page: int
    page_size: int
    items: list[MyWordOut]


class MyWordCsvRequest(BaseModel):
    """화면이 파일을 읽어 글자(text)로 보낸다. 파일 업로드 전용 라이브러리를 새로 깔지 않으려는 선택."""

    csv_text: str = Field(max_length=CSV_TEXT_MAX_LENGTH)


class MyWordCsvResponse(BaseModel):
    inserted: int  # 새로 들어간 단어
    updated: int  # 이미 있어서 뜻을 덮어쓴 단어
    duplicate_in_file: int  # 파일 안에서 같은 단어가 또 나와 앞 줄을 버린 수
    total_count: int  # 가져온 뒤 내 단어 전체 수


class MyWordStudyItem(BaseModel):
    id: int
    headword: str
    meaning_ko: str


class MyWordStudyResponse(BaseModel):
    due_total: int  # 오늘 공부할 차례인 전체 수
    items: list[MyWordStudyItem]  # 이번 회차(최대 20개)


class MyWordReviewRequest(BaseModel):
    rating: Literal["dont_know", "unsure", "know"]


class MyWordReviewResponse(BaseModel):
    id: int
    interval_days: int
    next_review_date: date
