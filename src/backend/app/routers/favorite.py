# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 즐겨찾기 API: 담기·해제·목록·다시 학습 (이슈 #22)
# 파일 위치: src/backend/app/routers/favorite.py
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.favorite import FavoriteStudyResponse, FavoritesResponse
from app.services import favorite_service

router = APIRouter(prefix="/favorites", tags=["즐겨찾기"])


@router.get("", response_model=FavoritesResponse)
def list_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return favorite_service.list_favorites(db, current_user)


@router.get("/study", response_model=FavoriteStudyResponse)
def study_words(
    limit: int = Query(10, ge=1, le=20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return favorite_service.get_study_words(db, current_user, limit)


@router.put("/{word_id}", status_code=204)
def add_favorite(word_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorite_service.add_favorite(db, current_user, word_id)
    return Response(status_code=204)


@router.delete("/{word_id}", status_code=204)
def remove_favorite(word_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorite_service.remove_favorite(db, current_user, word_id)
    return Response(status_code=204)
