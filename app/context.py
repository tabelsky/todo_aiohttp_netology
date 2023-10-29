from aiohttp import web

from models import Base, engine


async def init_db(app: web.Application):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
