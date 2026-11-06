# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필 수정·비밀번호 변경·이용권 요약·탈퇴 API (프로필 설정 설계서 3장, FR-PROFILE-01~05)
# 파일 위치: src/backend/app/routers/profile.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import clear_auth_cookie, create_access_token, set_auth_cookie
from app.models.user import User
from app.schemas.profile import PasswordChangeRequest, PlanSummaryResponse, ProfileRequest, WithdrawRequest
from app.schemas.study import UserResponse
from app.services import auth_service, profile_service

router = APIRouter(prefix="/me", tags=["프로필"])


@router.patch("/profile", response_model=UserResponse)
def update_profile(body: ProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = profile_service.update_profile(db, current_user, body)
    return UserResponse(user=auth_service.to_user_out(user))


@router.post("/password", status_code=204)
def change_password(
    body: PasswordChangeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    profile_service.change_password(db, current_user, body)
    response = Response(status_code=204)
    set_auth_cookie(response, create_access_token(current_user.id))  # 이 기기는 새 증표로 계속 로그인 상태
    return response


@router.get("/plan", response_model=PlanSummaryResponse)
def plan_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return profile_service.get_plan_summary(db, current_user)


@router.post("/withdraw", status_code=204)
def withdraw(body: WithdrawRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile_service.withdraw(db, current_user, body.password)
    response = Response(status_code=204)
    clear_auth_cookie(response)
    return response
