# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - DB 연결(엔진)과 요청마다 쓰는 세션을 만든다
# 파일 위치: src/backend/app/core/database.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

# 엔진: DB 와의 연결 통로. 만들 때는 아직 접속하지 않고, 처음 쓸 때 접속한다.
# pool_pre_ping: 재사용하는 연결이 끊겼는지 쓰기 전에 가볍게 확인
engine = create_engine(get_settings().database_url, pool_pre_ping=True)

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
