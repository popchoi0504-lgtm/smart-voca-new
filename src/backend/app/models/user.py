# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - users 표(회원) 모델 (데이터 설계서 4.1, FR-AUTH-01·04, FR-STUDY-04, FR-SUB-05)
# 파일 위치: src/backend/app/models/user.py
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    # 번호표(기본 키). Identity: DB 가 1, 2, 3 ... 순서로 자동 부여
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    # 로그인 ID. 소문자로 정리해서 저장하고, 같은 값이 두 번 들어가지 못하게 UNIQUE
    email: Mapped[str] = mapped_column(Text, unique=True)

    # 비밀번호 원문이 아니라 Argon2 해시 값만 저장한다
    password_hash: Mapped[str] = mapped_column(Text)

    # 하루에 배울 새 단어 수 설정 (기본 10, 1~50)
    daily_new_limit: Mapped[int] = mapped_column(SmallInteger, server_default="10")

    # 이용권 만료 시각. 비어 있거나 과거면 무료 회원
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 프로필 (이슈 #17). 비어 있으면 화면에서 이메일 앞부분·자동 배정 색을 쓴다
    nickname: Mapped[str | None] = mapped_column(Text)
    avatar_color: Mapped[str | None] = mapped_column(Text)
    # 탈퇴한 시각. 값이 있으면 익명화된 탈퇴 회원이라 로그인 증표가 있어도 통과시키지 않는다
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "avatar_color IN ('mint', 'lavender', 'yellow', 'pink', 'sky', 'orange')", name="avatar_color_allowed"
        ),
        # 잘못된 값은 서버 코드가 틀려도 DB 가 막는다 (이름: ck_users_daily_new_limit_range)
        CheckConstraint("daily_new_limit BETWEEN 1 AND 50", name="daily_new_limit_range"),
    )
