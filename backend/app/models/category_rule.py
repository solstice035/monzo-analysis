"""CategoryRule model for auto-categorisation rules."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account


class CategoryRule(Base, TimestampMixin):
    """Represents an auto-categorisation rule, scoped to an account."""

    __tablename__ = "category_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    conditions: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    target_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="category_rules")
