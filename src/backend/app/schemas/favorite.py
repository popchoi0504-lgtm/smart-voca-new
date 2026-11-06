# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 즐겨찾기 응답 양식 (이슈 #22)
# 파일 위치: src/backend/app/schemas/favorite.py
from datetime import date

from pydantic import BaseModel

from app.schemas.study import NewWordItem


class FavoriteItem(BaseModel):
    word_id: int
    headword: str
    part_of_speech: str
    meaning_ko: str
    example_en: str
    example_ko: str
    favorited_date: date  # 별표를 단 날 (한국 날짜)
    is_locked: bool  # 이용권 범위 밖이라 다시 학습할 수 없는 단어 (해제는 가능)


class FavoritesResponse(BaseModel):
    total_count: int
    items: list[FavoriteItem]


class FavoriteStudyResponse(BaseModel):
    items: list[NewWordItem]
    total_available: int  # 다시 학습할 수 있는(잠기지 않은) 즐겨찾기 전체 수
