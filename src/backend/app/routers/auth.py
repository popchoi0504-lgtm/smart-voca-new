# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 회원가입·로그인·로그아웃·내 정보 API (인터페이스 정의서 4.2, FR-AUTH-01~06)
# 파일 위치: src/backend/app/routers/auth.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import clear_auth_cookie, create_access_token, set_auth_cookie
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/signup", status_code=201, response_model=AuthResponse)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """회원가입. 성공하면 바로 로그인된 상태(쿠키 발급)로 만든다."""
    user = auth_service.signup(db, body.email, body.password, body.terms_version, body.agree_marketing)
    set_auth_cookie(response, create_access_token(user.id))
    return AuthResponse(user=auth_service.to_user_out(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, body.email, body.password)
    set_auth_cookie(response, create_access_token(user.id))
    return AuthResponse(user=auth_service.to_user_out(user))


@router.post("/logout", status_code=204)
def logout():
    """로그아웃. 이미 로그아웃된 상태여도 같은 결과(204)를 돌려준다."""
    response = Response(status_code=204)
    clear_auth_cookie(response)
    return response


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)):
    """지금 로그인한 회원의 정보. 로그인하지 않았으면 get_current_user 가 401 을 낸다."""
    return AuthResponse(user=auth_service.to_user_out(current_user))
