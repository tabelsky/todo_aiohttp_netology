from typing import Any

from sqlalchemy import Select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from errors import Conflict, NotFound
from models import MODEL, MODEL_TYPE


async def select_one(query: Select[Any], session: AsyncSession) -> MODEL:
    item = (await session.execute(query)).first()
    if not item:
        return None
    return item[0]


async def get_item_by_id(
    model: MODEL_TYPE, item_id: int, session: AsyncSession
) -> MODEL:
    item = await session.get(model, item_id)
    if item is None:
        raise NotFound(f"{model.__name__} not found")
    return item


async def add_item(item: MODEL, session: AsyncSession) -> MODEL:
    try:
        session.add(item)
        await session.commit()
    except IntegrityError as err:
        if err.orig.pgcode == "23505":
            raise Conflict(f"{item.__class__.__name__} already exists")
        else:
            raise err
    return item


async def create_item(model: MODEL_TYPE, payload: dict, session: AsyncSession) -> MODEL:
    item = model(**payload)
    item = await add_item(item, session)
    return item


async def delete_item(item: MODEL, session: AsyncSession):
    await session.delete(item)
    await session.commit()


async def update_item(item: MODEL, payload: dict, session: AsyncSession) -> MODEL:
    for field, value in payload.items():
        setattr(item, field, value)
    await add_item(item, session)
    return item


async def update_item_by_id(
    model: MODEL_TYPE, item_id: int, payload: dict, session: AsyncSession
) -> MODEL:
    item = get_item_by_id(model, item_id, session)
    await update_item(item, payload, session)
    return item
