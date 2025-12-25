import uuid
from datetime import UTC
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Uuid
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """Base Class For All SQLAlchemy Models.

    Inherits:
        DeclarativeBase

    Attributes:
        None

    Properties:
        None

    Methods:
        None
    """


class TimestampedModel(Base):
    """Abstract Base Model With ID And Timestamp Fields.

    Inherits:
        Base

    Attributes:
        id (uuid.UUID): Primary key UUID.
        created_at (datetime): Timestamp when record was created.
        updated_at (datetime): Timestamp when record was last updated.

    Properties:
        None

    Methods:
        None
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=lambda: datetime.now(tz=UTC),
        nullable=True,
    )


__all__: list[str] = ["Base", "TimestampedModel"]
