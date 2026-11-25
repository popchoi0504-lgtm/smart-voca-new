# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 즐겨찾기 담기·해제·목록·다시 학습 단어 뽑기의 업무 규칙 (이슈 #22)
# 파일 위치: src/backend/app/services/favorite_service.py
import logging

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import KST, now_utc
from app.models.favorite import Favorite
from app.models.user import User
from app.models.word import Word
from app.schemas.favorite import FavoriteItem, FavoriteStudyResponse, FavoritesResponse
from app.schemas.study import NewWordItem
from app.services.study_service import _plan_word_limit

logger = logging.getLogger("smart_voca.favorite")

MAX_STUDY_SIZE = 20  # 다시 학습 한 번의 분량


def add_favorite(db: Session, user: User, word_id: int) -> None:
    """별표를 켠다. 이미 켜져 있어도 성공(멱등). 이용권 범위 밖 단어는 못 켠다."""
    now = now_utc()
    word = db.get(Word, word_id)
    if word is None:
        raise AppError(404, "WORD_NOT_FOUND", "존재하지 않는 단어입니다.")
    if word.frequency_rank > _plan_word_limit(db, user, now):
        raise AppError(403, "PLAN_LIMIT_EXCEEDED", "무료 요금제에서는 이 단어를 즐겨찾기할 수 없습니다.")
    # ON CONFLICT DO NOTHING: 동시에 두 번 눌러도 오류 없이 한 행만 남는다
    db.execute(insert(Favorite).values(user_id=user.id, word_id=word_id, created_at=now).on_conflict_do_nothing())
    db.commit()
    logger.info("즐겨찾기 담기 user_id=%s word_id=%s", user.id, word_id)


def remove_favorite(db: Session, user: User, word_id: int) -> None:
    """별표를 끈다. 원래 없어도 성공(멱등). 이용권이 끝나도 해제는 언제나 가능하다."""
    favorite = db.get(Favorite, (user.id, word_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()
        logger.info("즐겨찾기 해제 user_id=%s word_id=%s", user.id, word_id)


def list_favorites(db: Session, user: User) -> FavoritesResponse:
    """내 즐겨찾기 전체(최근에 단 순). 반드시 user_id 로 걸러 다른 회원 것이 섞이지 않게 한다."""
    plan_limit = _plan_word_limit(db, user, now_utc())
    rows = db.execute(
        select(Word, Favorite.created_at)
        .join(Favorite, Favorite.word_id == Word.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc(), Word.id.desc())
    ).all()
    items = [
        FavoriteItem(
            word_id=word.id, headword=word.headword, part_of_speech=word.part_of_speech,
            meaning_ko=word.meaning_ko, example_en=word.example_en, example_ko=word.example_ko,
            favorited_date=created_at.astimezone(KST).date(), is_locked=word.frequency_rank > plan_limit,
        )
        for word, created_at in rows
    ]
    return FavoritesResponse(total_count=len(items), items=items)


def get_study_words(db: Session, user: User, limit: int) -> FavoriteStudyResponse:
    """다시 학습할 즐겨찾기 단어를 무작위로 최대 limit 개. 잠긴(이용권 밖) 단어는 뺀다.
    복습 일정(SM-2)은 건드리지 않는 연습용이라 기록을 쓰지 않는다."""
    plan_limit = _plan_word_limit(db, user, now_utc())
    condition = (Favorite.user_id == user.id, Word.frequency_rank <= plan_limit)
    total = db.scalar(select(func.count()).select_from(Favorite).join(Word, Favorite.word_id == Word.id).where(*condition))
    words = db.scalars(
        select(Word).join(Favorite, Favorite.word_id == Word.id).where(*condition)
        .order_by(func.random()).limit(min(limit, MAX_STUDY_SIZE))
    ).all()
    items = [
        NewWordItem(
            word_id=word.id, headword=word.headword, part_of_speech=word.part_of_speech, meaning_ko=word.meaning_ko,
            example_en=word.example_en, example_ko=word.example_ko, frequency_rank=word.frequency_rank,
        )
        for word in words
    ]
    return FavoriteStudyResponse(items=items, total_available=total)
