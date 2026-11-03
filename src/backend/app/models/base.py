# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - 모든 DB 표(모델)의 공통 부모 클래스와 제약 이름 규칙
# 파일 위치: src/backend/app/models/base.py
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# 제약 조건(기본 키, 외래 키, UNIQUE 등)의 이름을 규칙으로 정해 둔다.
# 이름이 정해져 있어야 나중에 표를 바꿀 때(Alembic) 어떤 제약을 지울지 정확히 가리킬 수 있다.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """모든 모델이 상속하는 부모. 여기에 모인 정보(metadata)를 보고 Alembic 이 표 변경을 계산한다."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
