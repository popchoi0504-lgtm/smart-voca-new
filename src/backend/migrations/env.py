# -*- coding: utf-8 -*-
# 2026-11-03 - smart-voca - Alembic 실행 설정: .env 의 DB 주소와 우리 모델(Base.metadata)을 연결한다
# 파일 위치: src/backend/migrations/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import get_settings
from app.models.base import Base

# 새 모델(표)을 만들면 여기에서 불러와야 Alembic 이 그 표를 알게 된다.
from app.models import user  # noqa: F401  (users 표, VS-1)
from app.models import word  # noqa: F401  (words 표, VS-2)
from app.models import user_word  # noqa: F401  (user_words 표, VS-3)
from app.models import review_log  # noqa: F401  (review_logs 표, VS-3)
from app.models import payment  # noqa: F401  (payments 표, VS-5)
from app.models import ai_usage  # noqa: F401  (ai_usages 표, 이슈 #16)
from app.models import favorite  # noqa: F401  (favorites 표, 이슈 #22)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 명령행 등에서 주소를 따로 주지 않았으면 .env 의 서비스 DB 주소를 쓴다
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    # disable_existing_loggers=False: 이미 설정된 서버 로그를 Alembic 이 꺼 버리지 않게 한다
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# autogenerate(모델과 DB 를 비교해 변경 파일 자동 작성)가 참고하는 모델 정보
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
