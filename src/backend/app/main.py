# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - FastAPI 앱을 만들고 로그·오류 처리·라우터를 한곳에 조립하는 시작점
# 파일 위치: src/backend/app/main.py
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import PROJECT_ROOT, get_settings
from app.core.database import SessionLocal, init_db
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.seed import seed_words_if_empty
from app.routers import ai, auth, favorite, health, my_word, profile, progress, quiz, study, subscription

request_logger = logging.getLogger("smart_voca.request")

# 화면(React)을 빌드한 결과물 위치. 서버 하나가 화면과 API 를 함께 내보낸다 (포트 8080 하나만 열기 때문)
FRONTEND_DIST = PROJECT_ROOT / "src" / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """서버가 켜질 때 한 번: 표를 만들고, 단어가 비어 있으면 기본 단어를 넣는다."""
    init_db()
    if get_settings().seed_words_on_start:
        with SessionLocal() as session:
            seed_words_if_empty(session)
    yield


def create_app() -> FastAPI:
    """앱을 만든다. 함수로 감싸 두면 테스트에서 새 앱을 쉽게 만들 수 있다."""
    setup_logging()

    # 자동 문서 주소도 /api 아래에 둔다 → 개발 서버의 프록시를 통해 브라우저에서 볼 수 있다
    app = FastAPI(
        title="smart-voca API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """모든 요청의 방식, 주소, 결과 코드, 걸린 시간을 로그로 남긴다. (본문·쿠키는 남기지 않는다)"""
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        request_logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, elapsed_ms)
        return response

    # 모든 API 는 /api 로 시작한다 (인터페이스 정의서 2장)
    app.include_router(health.router, prefix="/api", tags=["시스템"])
    app.include_router(auth.router, prefix="/api")
    app.include_router(study.study_router, prefix="/api")
    app.include_router(study.me_router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.include_router(quiz.router, prefix="/api")
    app.include_router(progress.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(favorite.router, prefix="/api")
    app.include_router(my_word.router, prefix="/api")
    app.include_router(subscription.subscription_router, prefix="/api")
    app.include_router(subscription.payments_router, prefix="/api")
    _mount_frontend(app, FRONTEND_DIST)
    return app


def _mount_frontend(app: FastAPI, dist_dir: Path) -> None:
    """빌드된 화면 파일이 있으면 같이 내보낸다. 없으면(개발 중) API 만 동작한다.

    화면 주소는 # 뒤에 붙는 방식(HashRouter)이라 서버는 첫 화면(index.html)과 정적 파일만 주면 된다.
    """
    index_file = dist_dir / "index.html"
    if not index_file.is_file():
        return

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(index_file)

    app.mount("/", StaticFiles(directory=dist_dir), name="frontend")


app = create_app()
