from datetime import datetime
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    pass

class AllowedUser(Base):
    __tablename__ = "allowed_users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(nullable=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<AllowedUser(user_id={self.user_id}, username={self.username})>"
