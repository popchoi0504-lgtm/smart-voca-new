# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 내 단어 API: 등록·목록/검색·수정·삭제·CSV 가져오기·공부 (이슈 #24, VOCA-FR-001~004)
# 파일 위치: src/backend/app/routers/my_word.py
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.my_word import (
    MyWordCsvRequest, MyWordCsvResponse, MyWordListResponse, MyWordOut, MyWordRequest, MyWordReviewRequest,
    MyWordReviewResponse, MyWordStudyResponse,
)
from app.services import my_word_service

router = APIRouter(prefix="/my-words", tags=["내 단어"])


@router.get("", response_model=MyWordListResponse)
def list_words(
    q: str = Query("", max_length=100), page: int = Query(1, ge=1),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return my_word_service.list_words(db, current_user, q, page)


@router.post("", response_model=MyWordOut, status_code=201)
def create_word(body: MyWordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return my_word_service.create_word(db, current_user, body)


# 고정 주소(/import, /study)는 /{word_id} 보다 위에 둔다: 위에 있어야 "study" 를 번호로 착각하지 않는다
@router.post("/import", response_model=MyWordCsvResponse)
def import_csv(body: MyWordCsvRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return my_word_service.import_csv(db, current_user, body.csv_text)


@router.get("/study", response_model=MyWordStudyResponse)
def study_words(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return my_word_service.get_study_words(db, current_user)


@router.put("/{word_id}", response_model=MyWordOut)
def update_word(
    word_id: int, body: MyWordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return my_word_service.update_word(db, current_user, word_id, body)


@router.delete("/{word_id}", status_code=204)
def delete_word(word_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    my_word_service.delete_word(db, current_user, word_id)
    return Response(status_code=204)


@router.post("/{word_id}/review", response_model=MyWordReviewResponse)
def review_word(
    word_id: int, body: MyWordReviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return my_word_service.review_word(db, current_user, word_id, body.rating)
