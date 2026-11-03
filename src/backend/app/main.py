# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - FastAPI 앱을 만들고 로그·오류 처리·라우터를 한곳에 조립하는 시작점
# 파일 위치: src/backend/app/main.py
import logging
import time

from fastapi import FastAPI, Request

from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.routers import health

request_logger = logging.getLogger("smart_voca.request")


def create_app() -> FastAPI:
    """앱을 만든다. 함수로 감싸 두면 테스트에서 새 앱을 쉽게 만들 수 있다."""
    setup_logging()

    # 자동 문서 주소도 /api 아래에 둔다 → 개발 서버의 프록시를 통해 브라우저에서 볼 수 있다
    app = FastAPI(
        title="smart-voca API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
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
    return app


app = create_app()
