# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - 모든 DB 표(모델)의 공통 부모 클래스와 제약 이름 규칙
# 파일 위치: src/backend/app/models/base.py
from datetime import timezone

from sqlalchemy import BigInteger, DateTime, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

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


# 기본 키 번호표 타입. SQLite 는 "INTEGER PRIMARY KEY" 일 때만 번호를 자동으로 붙여 주므로 SQLite 에서는 Integer 로 바꿔 쓴다.
BigIntId = BigInteger().with_variant(Integer(), "sqlite")


class UtcDateTime(TypeDecorator):
    """항상 UTC 시간대 정보가 붙은 시각으로 저장·조회하는 타입.

    SQLite 는 시간대 정보를 저장하지 못해 읽을 때 정보가 빠진 시각이 돌아온다. 그러면 .astimezone(KST) 가
    컴퓨터 시간대를 기준으로 계산해 날짜가 틀어질 수 있으므로, 저장은 UTC 로 바꿔서 하고 읽을 때 UTC 표시를 다시 붙인다.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value  # 시간대 정보가 없으면 이미 UTC 로 본다
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)
