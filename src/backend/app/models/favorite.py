# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - favorites 표(회원이 별표로 모은 단어) 모델 (즐겨찾기 설계, 이슈 #22)
# 파일 위치: src/backend/app/models/favorite.py
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Favorite(Base):
    """행이 있으면 별표가 켜진 단어다. 학습 여부(user_words)와는 별개: 아직 배우지 않은 카드에도 별표를 달 수 있다."""

    __tablename__ = "favorites"

    # (user_id, word_id) 가 기본 키: 같은 단어에 별표가 두 번 달리지 않는다
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    word_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("words.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
