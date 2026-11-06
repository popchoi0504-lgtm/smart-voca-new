# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - AI 선생님 질문 API (AI 선생님 설계서 5장)
# 파일 위치: src/backend/app/routers/ai.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.provider import TeacherProvider, get_teacher_provider
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import TeacherRequest, TeacherResponse
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI 선생님"])


@router.post("/teacher", response_model=TeacherResponse)
def ask_teacher(
    body: TeacherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: TeacherProvider = Depends(get_teacher_provider),
):
    return ai_service.ask_teacher(db, current_user, body, provider)
