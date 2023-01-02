import json
from typing import Optional

from fastapi import HTTPException, Query
from sqlalchemy import asc, desc, text
from sqlalchemy.ext.declarative import DeclarativeMeta

from app.schemas.request_params import RequestParams


def parse_react_admin_params(model: DeclarativeMeta) -> RequestParams:
    """Parses sort and range parameters coming from a react-admin request"""

    def inner(
        sort_: Optional[str] = Query(
            None,
            alias="sort",
            description='Format: `["field_name", "direction"]`',
            example='["id", "ASC"]',
        ),
        range_: Optional[str] = Query(
            None,
            alias="range",
            description="Format: `[start, end]`",
            example="[0, 10]",
        ),
        filter_: Optional[str] = Query(
            None,
            alias="filter",
            description='Format: `["field_name", "value"]`',
            example='["id", [1]]',
        ),
    ):
        skip, limit = 0, 10
        if range_:
            start, end = json.loads(range_)
            skip, limit = start, (end - start + 1)

        order_by = desc(model.id)
        if sort_:
            sort_column, sort_order = json.loads(sort_)
            if sort_order.lower() == "asc":
                direction = asc
            elif sort_order.lower() == "desc":
                direction = desc
            else:
                raise HTTPException(400, f"Invalid sort direction {sort_order}")
            if type(sort_column) == list:
                order_by = direction(model.__table__.c[sort_column[0] + "_id"])
            else:
                order_by = direction(model.__table__.c[sort_column])

        filter = text("1=1")

        if filter_ and filter_ != "false":
            filter_column, filter_value = json.loads(filter_)
            if type(filter_column) == list:
                filter_column = filter_column[0] + "_id"
            filter = model.__table__.c[filter_column].in_(filter_value)

        return RequestParams(skip=skip, limit=limit, order_by=order_by, filter=filter)

    return inner
