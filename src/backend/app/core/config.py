# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - .env 에서 설정을 읽어 오는 모듈 (코드에 비밀값을 쓰지 않기 위함)
# 파일 위치: src/backend/app/core/config.py
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
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

    # DB: SQLite 파일 위치. 서버에서는 환경변수 DB_PATH=/data/voca.db 로 준다 (교수 요건 VOCA-NFR-002, R-06)
    db_path: Path = PROJECT_ROOT / "data" / "voca.db"
    # 처음 실행해서 words 표가 비어 있으면 data/words/toeic_2000.csv 를 자동으로 넣는다 (테스트에서는 끈다)
    seed_words_on_start: bool = True

    # 로그인 토큰 서명 비밀값. 환경변수 SECRET_KEY(서버 규칙 R-08), 예전 이름 JWT_SECRET 도 받는다.
    # 둘 다 없으면 서버가 켜질 때 무작위로 만든다(서버를 다시 켜면 로그인 상태가 풀릴 뿐 기능에는 문제 없음).
    jwt_secret: str = Field(default="", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
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

    # 로그 파일 위치. 서버에서는 쓰기가 /data·/tmp 에만 되므로 환경변수 LOG_DIR=/tmp/logs 로 바꾼다
    log_dir: Path = PROJECT_ROOT / "logs"

    @property
    def database_url(self) -> str:
        """SQLAlchemy 가 쓰는 DB 주소. 파일 경로(DB_PATH)에서 만든다."""
        return f"sqlite:///{Path(self.db_path).as_posix()}"


@lru_cache
def get_settings() -> Settings:
    """설정을 한 번만 읽어 재사용한다."""
    settings = Settings()
    if not settings.jwt_secret:
        settings.jwt_secret = secrets.token_urlsafe(48)
    return settings
