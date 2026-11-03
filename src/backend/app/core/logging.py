# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - 로그를 콘솔과 파일(logs/app.log)에 남기는 설정 (FR-SYS-02)
# 파일 위치: src/backend/app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging() -> None:
    """로그 설정. 여러 번 불러도 같은 핸들러가 중복으로 붙지 않는다.

    주의: 비밀번호, 토큰, 카드 정보는 절대 로그로 남기지 않는다.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, "_smart_voca_configured", False):
        return

    log_dir = get_settings().log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 파일이 1MB 를 넘으면 새 파일로 넘기고, 이전 파일은 3개까지만 보관
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger._smart_voca_configured = True  # type: ignore[attr-defined]
