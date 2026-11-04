# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - "로그인한 사람만" 통과시키는 공통 검사 함수 (FR-AUTH-06)
# 파일 위치: src/backend/app/core/dependencies.py
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import ACCESS_TOKEN_COOKIE, decode_access_token
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """쿠키의 로그인 증표를 확인해 현재 회원을 돌려준다. 증표가 없거나 위조·만료됐거나 회원이 없으면 401.

    로그인이 필요한 API 는 이 함수를 Depends 로 붙이기만 하면 보호된다.
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise AppError(401, "NOT_AUTHENTICATED", "로그인이 필요합니다.")
    return user
