# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - 모든 오류를 같은 모양의 JSON 으로 돌려주는 처리기 (FR-SYS-01, 인터페이스 정의서 3장)
# 파일 위치: src/backend/app/core/errors.py
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("smart_voca.errors")


class AppError(Exception):
    """우리 서비스가 의도해서 내는 오류. 코드·메시지·HTTP 상태를 함께 가진다."""

    def __init__(self, status_code: int, code: str, message: str, fields: list[dict] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields


def error_response(status_code: int, code: str, message: str, fields: list[dict] | None = None) -> JSONResponse:
    """오류 응답의 공통 모양: {"error": {"code": ..., "message": ..., "fields": [...]}}"""
    body: dict = {"code": code, "message": message}
    if fields:
        body["fields"] = fields
    return JSONResponse(status_code=status_code, content={"error": body})


def register_exception_handlers(app: FastAPI) -> None:
    """앱에 오류 처리기를 등록한다. 어떤 오류가 나도 응답 모양이 같아지고, 내부 정보는 화면에 나가지 않는다."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.fields)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            # loc 의 첫 항목은 "body" 같은 위치 표시라서 빼고, 나머지를 칸 이름으로 쓴다
            {"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return error_response(422, "VALIDATION_ERROR", "입력값을 확인해 주세요.", fields)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error_response(404, "NOT_FOUND", "요청한 주소를 찾을 수 없습니다.")
        if exc.status_code == 405:
            return error_response(405, "METHOD_NOT_ALLOWED", "허용되지 않는 요청 방식입니다.")
        return error_response(exc.status_code, f"HTTP_{exc.status_code}", "요청을 처리할 수 없습니다.")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # 자세한 내용(스택)은 로그에만 남기고, 사용자에게는 일반 메시지만 보낸다
        logger.exception("처리되지 않은 오류: %s %s", request.method, request.url.path)
        return error_response(500, "INTERNAL_ERROR", "서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요.")
