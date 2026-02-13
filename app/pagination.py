import base64
import uuid
from datetime import datetime
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


def encode_cursor(created_at: datetime, record_id: uuid.UUID) -> str:
    """Encode a (created_at, id) pair into a URL-safe base64 cursor string."""
    raw = f"{created_at.isoformat()}|{record_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decode a base64 cursor string back into (created_at, id)."""
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts_str, id_str = raw.split("|", 1)
    return datetime.fromisoformat(ts_str), uuid.UUID(id_str)


def apply_cursor(
    query: Select,
    created_at_col: InstrumentedAttribute,
    id_col: InstrumentedAttribute,
    cursor: str | None,
    limit: int,
) -> tuple[Select, str | None]:
    """Apply cursor-based pagination to a query.

    Returns (modified_query, None). The caller should use `paginate()` instead
    for the full flow, or call this for just the query modification.
    """
    if cursor is not None:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        query = query.where(
            or_(
                created_at_col < cursor_created_at,
                (created_at_col == cursor_created_at) & (id_col < cursor_id),
            )
        )
    return query.order_by(created_at_col.desc(), id_col.desc()).limit(limit + 1)


async def paginate(
    db: AsyncSession,
    query: Select,
    created_at_col: InstrumentedAttribute,
    id_col: InstrumentedAttribute,
    cursor: str | None,
    limit: int,
) -> tuple[Sequence, str | None]:
    """Execute a paginated query and return (rows, next_cursor)."""
    query = apply_cursor(query, created_at_col, id_col, cursor, limit)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = encode_cursor(
            getattr(last, created_at_col.key),
            getattr(last, id_col.key),
        )

    return rows, next_cursor
