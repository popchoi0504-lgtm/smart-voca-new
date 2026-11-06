# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 테스트 공통 준비물: 테스트 전용 DB 준비, 테스트마다 표 비우기, API 호출용 클라이언트
# 파일 위치: src/backend/tests/conftest.py
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models import user  # noqa: F401  (모델을 불러와야 Base.metadata 에 표 목록이 채워진다)
from app.models import word  # noqa: F401
from app.models import ai_usage, payment, review_log, user_word  # noqa: F401
from app.models.base import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB_NAME = "smart_voca_test"


@pytest.fixture(scope="session")
def test_engine():
    """테스트 전용 DB 를 Alembic 변경 파일로 처음부터 만든다. (변경 파일 자체도 함께 검증된다)"""
    test_url = get_settings().test_database_url
    # 안전장치: 실수로 개발용 DB(smart_voca)의 데이터를 지우는 일을 막는다
    if not test_url or make_url(test_url).database != TEST_DB_NAME:
        pytest.exit(f"TEST_DATABASE_URL 이 {TEST_DB_NAME} 를 가리키지 않아 테스트를 중단합니다.", returncode=2)

    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_url)
    command.downgrade(alembic_config, "base")  # 이전 테스트가 남긴 표를 모두 지우고
    command.upgrade(alembic_config, "head")  # 최신 구조로 다시 만든다

    engine = create_engine(test_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session_factory(test_engine):
    """테스트 시작 때마다 모든 표를 비워서, 테스트끼리 데이터가 섞이지 않게 한다."""
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with test_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    return sessionmaker(bind=test_engine, autoflush=False)


@pytest.fixture
def db_session(db_session_factory):
    """테스트 코드에서 DB 내용을 직접 확인하거나 준비할 때 쓰는 세션."""
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture
def api_client(db_session_factory):
    """실제 API 를 부르는 가짜 브라우저. DB 는 테스트 전용 DB 로 바꿔 끼운다. 쿠키를 자동으로 기억한다."""

    def override_get_db():
        session = db_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
