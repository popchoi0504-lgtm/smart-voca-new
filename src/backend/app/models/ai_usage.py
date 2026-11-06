# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - ai_usages 표(회원별 하루 AI 선생님 사용 횟수) 모델 (AI 선생님 설계서 4장, FR-AI-05)
# 파일 위치: src/backend/app/models/ai_usage.py
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AiUsage(Base):
    """회원이 한국 날짜 기준 하루에 AI 선생님을 몇 번 썼는지. 대화 내용은 저장하지 않는다(개인정보 최소화)."""

    __tablename__ = "ai_usages"

    # (user_id, usage_date) 가 합쳐서 기본 키: 한 회원의 하루는 행 하나, 중복 행이 생길 수 없다
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    usage_date: Mapped[date] = mapped_column(Date, primary_key=True)
    call_count: Mapped[int] = mapped_column(SmallInteger, server_default="0")

    __table_args__ = (CheckConstraint("call_count >= 0", name="call_count_non_negative"),)
