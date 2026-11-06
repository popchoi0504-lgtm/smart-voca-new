# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - .env 에서 설정을 읽어 오는 모듈 (코드에 비밀값을 쓰지 않기 위함)
# 파일 위치: src/backend/app/core/config.py
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트(.env 가 있는 곳). 이 파일은 src/backend/app/core/ 아래에 있으므로 4단계 위
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """환경 변수(.env)에서 읽은 설정값. 이름은 대소문자 구분 없이 .env 의 키와 맞춰진다."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env 에 이 클래스가 모르는 키(POSTGRES_* 등)가 있어도 무시
    )

    # DB (기본값 없음: 없으면 서버가 시작할 때 바로 오류를 낸다)
    database_url: str
    test_database_url: str = ""

    # 로그인 토큰 (VS-1 에서 사용)
    jwt_secret: str
    jwt_expire_days: int = 7
    cookie_secure: bool = False  # https 로 배포할 때는 반드시 True

    # 요금제 (대표 결정 2026-11-03)
    free_word_limit: int = 250
    premium_price_krw: int = 4900
    premium_pass_days: int = 30
    refund_window_days: int = 7  # 결제 후 이 기간 안, 프리미엄 단어를 쓰지 않았을 때만 환불

    # 결제 담당자: "toss"(토스 연동) 또는 "fake"(가짜 결제, FR-SUB-08)
    payment_provider: str = "toss"

    # 토스페이먼츠 테스트 키 (VS-5 에서 사용, 대표가 .env 에 직접 입력)
    toss_client_key: str = ""
    toss_secret_key: str = ""

    # AI 선생님 (이슈 #16). provider: "fake"(가짜 답변, 개발·테스트용) 또는 "gemini"(실제 호출)
    ai_provider: str = "fake"
    gemini_api_key: str = ""
    gemini_model: str = ""  # 모델 이름은 문서마다 달라서 코드에 쓰지 않고 .env 로 정한다
    ai_teacher_enabled: bool = True  # False 면 기능을 끈다(발표 직전 장애 대비)
    ai_free_daily_limit: int = 10  # 대표 결정 2026-11-06
    ai_premium_daily_limit: int = 50

    # 로그 파일 위치
    log_dir: Path = PROJECT_ROOT / "logs"


@lru_cache
def get_settings() -> Settings:
    """설정을 한 번만 읽어 재사용한다."""
    return Settings()
