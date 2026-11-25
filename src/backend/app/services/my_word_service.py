# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 내 단어 등록·목록·수정·삭제·CSV 가져오기·공부(복습)의 업무 규칙 (이슈 #24, VOCA-FR-001~004)
# 파일 위치: src/backend/app/services/my_word_service.py
import logging
from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import KST, now_utc, to_kst, today_kst
from app.core_logic.quality import flashcard_quality
from app.core_logic.sm2 import Sm2State, calculate_next
from app.models.my_word import MyWord
from app.models.user import User
from app.schemas.my_word import (
    MyWordCsvResponse, MyWordListResponse, MyWordOut, MyWordRequest, MyWordReviewResponse, MyWordStudyItem,
    MyWordStudyResponse,
)
from app.services.my_word_csv import parse_voca_csv

logger = logging.getLogger("smart_voca.my_word")

PAGE_SIZE = 50
STUDY_SIZE = 20  # 한 번에 공부하는 분량


def _key(headword: str) -> str:
    """같은 단어인지 비교하는 값. 대소문자를 무시한다."""
    return headword.strip().lower()


def _to_out(word: MyWord) -> MyWordOut:
    return MyWordOut(
        id=word.id, headword=word.headword, meaning_ko=word.meaning_ko,
        next_review_date=word.next_review_date, created_date=to_kst(word.created_at).date(),
    )


def _get_own(db: Session, user: User, word_id: int) -> MyWord:
    """내 단어만 꺼낸다. 남의 단어도 '없음'(404)으로 답해서 그런 번호가 있는지조차 알려 주지 않는다."""
    word = db.get(MyWord, word_id)
    if word is None or word.user_id != user.id:
        raise AppError(404, "MY_WORD_NOT_FOUND", "존재하지 않는 단어입니다.")
    return word


def _duplicate_error() -> AppError:
    return AppError(409, "MY_WORD_DUPLICATE", "이미 등록한 단어예요.")


def create_word(db: Session, user: User, body: MyWordRequest) -> MyWordOut:
    now = now_utc()
    word = MyWord(
        user_id=user.id, headword=body.headword, headword_key=_key(body.headword), meaning_ko=body.meaning_ko,
        next_review_date=today_kst(), created_at=now, updated_at=now,
        repetitions=0, interval_days=0,
    )
    db.add(word)
    try:
        db.commit()
    except IntegrityError:  # (user_id, headword_key) UNIQUE 에 걸림 = 이미 있는 단어
        db.rollback()
        raise _duplicate_error() from None
    return _to_out(word)


def list_words(db: Session, user: User, query: str, page: int) -> MyWordListResponse:
    """영단어 또는 뜻에 검색어가 들어간 내 단어 목록(영단어 알파벳순). 검색어가 비면 전체."""
    conditions = [MyWord.user_id == user.id]
    query = query.strip()
    if query:
        # LIKE 의 특수문자(% _)가 검색어에 있어도 글자 그대로 찾도록 막는다
        escaped = query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        conditions.append(
            or_(MyWord.headword_key.like(pattern, escape="\\"), func.lower(MyWord.meaning_ko).like(pattern, escape="\\"))
        )
    total = db.scalar(select(func.count()).select_from(MyWord).where(*conditions)) or 0
    words = db.scalars(
        select(MyWord).where(*conditions).order_by(MyWord.headword_key, MyWord.id)
        .limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)
    ).all()
    return MyWordListResponse(total_count=total, page=page, page_size=PAGE_SIZE, items=[_to_out(w) for w in words])


def update_word(db: Session, user: User, word_id: int, body: MyWordRequest) -> MyWordOut:
    word = _get_own(db, user, word_id)
    word.headword, word.headword_key, word.meaning_ko = body.headword, _key(body.headword), body.meaning_ko
    word.updated_at = now_utc()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _duplicate_error() from None
    return _to_out(word)


def delete_word(db: Session, user: User, word_id: int) -> None:
    db.delete(_get_own(db, user, word_id))
    db.commit()


def import_csv(db: Session, user: User, csv_text: str) -> MyWordCsvResponse:
    """CSV 를 가져온다. 방침: 영단어가 같으면(대소문자 무시) 뜻을 덮어쓴다. 파일 안에서 같은 단어가 또 나오면 나중 줄이 이긴다.
    한 트랜잭션이라 중간에 실패하면 하나도 반영되지 않는다."""
    parsed = parse_voca_csv(csv_text)
    latest_by_key: dict[str, tuple[str, str]] = {}  # 단어 키 → (영단어, 뜻): 같은 키가 또 나오면 덮어써서 나중 줄만 남긴다
    for _line, headword, meaning in parsed:
        latest_by_key[_key(headword)] = (headword, meaning)
    duplicate_in_file = len(parsed) - len(latest_by_key)

    existing = {word.headword_key: word for word in db.scalars(select(MyWord).where(MyWord.user_id == user.id))}
    now, today = now_utc(), today_kst()
    inserted = updated = 0
    for key, (headword, meaning) in latest_by_key.items():
        word = existing.get(key)
        if word is None:
            db.add(MyWord(user_id=user.id, headword=headword, headword_key=key, meaning_ko=meaning,
                          next_review_date=today, created_at=now, updated_at=now, repetitions=0, interval_days=0))
            inserted += 1
        elif word.meaning_ko != meaning:
            word.meaning_ko, word.updated_at = meaning, now  # 복습 기록은 그대로 둔다
            updated += 1
    db.commit()
    total = db.scalar(select(func.count()).select_from(MyWord).where(MyWord.user_id == user.id)) or 0
    logger.info("내 단어 CSV user_id=%s 새로 %d 덮어씀 %d 파일 내 중복 %d", user.id, inserted, updated, duplicate_in_file)
    return MyWordCsvResponse(inserted=inserted, updated=updated, duplicate_in_file=duplicate_in_file, total_count=total)


def get_study_words(db: Session, user: User) -> MyWordStudyResponse:
    """오늘(한국 날짜) 공부할 차례인 단어를 오래 기다린 순으로 최대 20개 준다."""
    due = (MyWord.user_id == user.id, MyWord.next_review_date <= today_kst())
    due_total = db.scalar(select(func.count()).select_from(MyWord).where(*due)) or 0
    words = db.scalars(select(MyWord).where(*due).order_by(MyWord.next_review_date, MyWord.id).limit(STUDY_SIZE)).all()
    return MyWordStudyResponse(
        due_total=due_total, items=[MyWordStudyItem(id=w.id, headword=w.headword, meaning_ko=w.meaning_ko) for w in words]
    )


def review_word(db: Session, user: User, word_id: int, rating: str) -> MyWordReviewResponse:
    """평가(몰랐음/애매함/알았음)를 SM-2 로 계산해 다음 복습일을 정한다. 공용 학습과 같은 규칙을 그대로 쓴다."""
    word = _get_own(db, user, word_id)
    now = now_utc()
    new_state = calculate_next(
        Sm2State(word.repetitions, word.interval_days, word.ease_factor), flashcard_quality(rating)
    )
    word.repetitions, word.interval_days, word.ease_factor = new_state.repetitions, new_state.interval_days, new_state.ease_factor
    word.next_review_date = now.astimezone(KST).date() + timedelta(days=new_state.interval_days)
    word.last_reviewed_at = now
    db.commit()
    return MyWordReviewResponse(id=word.id, interval_days=word.interval_days, next_review_date=word.next_review_date)
