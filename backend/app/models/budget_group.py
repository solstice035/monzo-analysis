"""BudgetGroup model for organizing budgets into hierarchical groups."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.budget import Budget


class BudgetGroup(Base, TimestampMixin):
    """Represents a group of related budgets (e.g., 'Kids', 'Fixed Bills').

    Budget groups provide hierarchical organization for budgets,
    enabling roll-up calculations and dashboard grouping.
    """

    __tablename__ = "budget_groups"

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
        String(100),
        nullable=False,
    )
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="budget_groups")
    budgets: Mapped[list["Budget"]] = relationship(
        "Budget",
        back_populates="group",
        cascade="all, delete-orphan",
    )
