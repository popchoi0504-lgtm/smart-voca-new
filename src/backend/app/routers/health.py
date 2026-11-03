# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - 서버와 DB 가 살아 있는지 확인하는 API (GET /api/health, 인터페이스 정의서 4.7)
# 파일 위치: src/backend/app/routers/health.py
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger("smart_voca.health")
router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """DB 에 가장 가벼운 질문(select 1)을 던져 보고 대답이 오면 정상으로 본다."""
    try:
        db.execute(text("select 1"))
    except Exception:
        # DB 오류 내용은 로그에만 남기고, 응답은 정해진 모양(503)으로 돌려준다
        logger.exception("DB 상태 확인 실패")
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
    return {"status": "ok", "db": "ok"}
