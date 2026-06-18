"""Generic ORM -> dict serialization for API responses."""
from sqlalchemy import inspect
from datetime import datetime


def row_to_dict(obj) -> dict:
    out = {}
    for col in inspect(obj).mapper.column_attrs:
        val = getattr(obj, col.key)
        if isinstance(val, datetime):
            val = val.isoformat()
        out[col.key] = val
    return out


def rows(objs) -> list[dict]:
    return [row_to_dict(o) for o in objs]
