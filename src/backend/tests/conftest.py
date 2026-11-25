# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 테스트 공통 준비물: 테스트 전용 DB 준비, 테스트마다 표 비우기, API 호출용 클라이언트
# 파일 위치: src/backend/tests/conftest.py
import os
import tempfile
from pathlib import Path

# 주의: app 을 불러오기 전에 설정해야 한다. 테스트는 임시 폴더의 SQLite 파일만 쓰고, 개발 DB(data/voca.db)는 건드리지 않는다.
_TEST_DIR = tempfile.mkdtemp(prefix="smart_voca_test_")
os.environ["DB_PATH"] = str(Path(_TEST_DIR) / "test.db")
os.environ["SEED_WORDS_ON_START"] = "false"  # 단어 2,000개 자동 적재를 끈다(테스트가 필요한 단어만 직접 만든다)
os.environ["LOG_DIR"] = str(Path(_TEST_DIR) / "logs")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import engine, get_db, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_engine():
    """테스트 전용 SQLite 파일(임시 폴더)에 표를 처음부터 만든다."""
    # 안전장치: 설정이 임시 폴더를 가리키지 않으면 개발 DB 를 지울 수 있으므로 중단한다
    if Path(get_settings().db_path).parent != Path(_TEST_DIR):
        pytest.exit("DB_PATH 가 테스트용 임시 폴더를 가리키지 않아 테스트를 중단합니다.", returncode=2)
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session_factory(test_engine):
    """테스트 시작 때마다 모든 표를 비워서, 테스트끼리 데이터가 섞이지 않게 한다. 번호표(id)도 1부터 다시 시작한다."""
    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):  # 자식 표부터 지워야 외래 키에 걸리지 않는다
            connection.execute(table.delete())
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
