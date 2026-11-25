# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - DB 연결(엔진)과 요청마다 쓰는 세션을 만든다
# 파일 위치: src/backend/app/core/database.py
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings



def make_engine(database_url: str) -> Engine:
    """SQLite 엔진을 만든다. 요청마다 다른 스레드에서 쓰므로 check_same_thread 를 끄고, 연결할 때마다 외래 키 검사를 켠다."""
    new_engine = create_engine(database_url, connect_args={"check_same_thread": False, "timeout": 30})

    @event.listens_for(new_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        # SQLite 는 기본으로 외래 키(ON DELETE CASCADE 등)를 검사하지 않아서 연결마다 켜 줘야 한다
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return new_engine


# 엔진: DB 와의 연결 통로. 만들 때는 아직 접속하지 않고, 처음 쓸 때 접속한다.
_settings = get_settings()
_settings.db_path.parent.mkdir(parents=True, exist_ok=True)  # data/ 또는 /data 폴더가 없으면 만든다
engine = make_engine(_settings.database_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """요청 하나가 쓰는 DB 세션을 열고, 요청이 끝나면 반드시 닫는다.

    FastAPI 의 Depends(get_db) 로 라우터에 주입한다. 테스트에서는 이 함수를 다른 것으로 바꿔 끼울 수 있다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine: Engine | None = None) -> None:
    """처음 실행할 때 필요한 표를 모두 만든다. 이미 있는 표는 건드리지 않는다. (VOCA-NFR-003: 빈 DB 에서 시작 가능)"""
    from app.models import ai_usage, favorite, payment, review_log, user, user_word, word  # noqa: F401  (표 목록을 채우기 위해)
    from app.models.base import Base

    Base.metadata.create_all(target_engine or engine)
