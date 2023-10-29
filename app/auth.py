import datetime

import bcrypt
from aiohttp.web import View
from sqlalchemy import select

from config import TOKEN_TTL
from crud import select_one
from errors import Forbidden, Unauthorized
from models import MODEL, Token


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def check_token(handler):
    async def wrapper(view: View):
        token_uid = view.request.headers.get("Authorization")
        if token_uid is None:
            raise Unauthorized("token not found")
        token_query = select(Token).where(
            Token.token == token_uid,
            Token.creation_time
            > datetime.datetime.now() - datetime.timedelta(seconds=TOKEN_TTL),
        )

        token = await select_one(token_query, view.session)

        if token is None:
            raise Unauthorized("invalid token")

        view.request.token = token
        return await handler(view)

    return wrapper


def check_owner(item: MODEL, user_id: int):
    if item.user_id != user_id:
        raise Forbidden("access denied")
