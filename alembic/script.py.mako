"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

${imports if imports else ""}

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade Schema.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade Schema.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    ${downgrades if downgrades else "pass"}
