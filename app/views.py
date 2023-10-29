from aiohttp import web
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import check_owner, check_password, check_token, hash_password
from crud import create_item, delete_item, get_item_by_id, select_one, update_item
from errors import Unauthorized
from models import Todo, Token, User
from schema import SCHEMA_MODEL, CreateTodo, CreateUser, Login, PatchUser, UpdateTodo
from tools import validate


class BaseView(web.View):
    @property
    def session(self) -> AsyncSession:
        return self.request.session

    @property
    def token(self) -> Token:
        return self.request.token

    @property
    def user(self) -> User:
        return self.request.token.user

    @property
    def is_authorized(self) -> bool:
        return hasattr(self.request, "token")

    async def validated_json(self, schema: SCHEMA_MODEL):
        raw_json = await self.request.json()
        return validate(schema, raw_json)


class UserView(BaseView):
    @check_token
    async def get(self):
        return web.json_response(self.user.dict)

    async def post(self):
        payload = await self.validated_json(CreateUser)
        payload["password"] = hash_password(payload["password"])
        user = await create_item(User, payload, self.session)
        return web.json_response({"id": user.id})

    @check_token
    async def patch(self):
        payload = await self.validated_json(PatchUser)
        user = await update_item(self.token.user, payload, self.session)
        return web.json_response({"id": user.id})

    @check_token
    async def delete(self):
        await delete_item(self.token.user, self.session)
        return web.json_response({"status": "ok"})


class LoginView(BaseView):
    async def post(self):
        payload = await self.validated_json(Login)
        query = select(User).where(User.name == payload["name"]).limit(1)
        user = await select_one(query, self.session)
        if not user:
            raise Unauthorized("invalid user or password")
        if check_password(payload["password"], user.password):
            token = await create_item(Token, {"user_id": user.id}, self.session)
            return web.json_response({"token": str(token.token)})
        raise Unauthorized("invalid user or password")


class TodoView(BaseView):
    @property
    def todo_id(self) -> int | None:
        todo_id = self.request.match_info.get("todo_id")
        return int(todo_id) if todo_id else None

    @check_token
    async def get(self):
        if self.todo_id is None:
            return web.json_response([todo.dict for todo in self.user.todos])
        todo = await get_item_by_id(Todo, self.todo_id, self.session)
        check_owner(todo, self.token.user_id)
        return web.json_response(todo.dict)

    @check_token
    async def post(self):
        payload = await self.validated_json(CreateTodo)
        todo = await create_item(
            Todo, dict(user_id=self.token.user_id, **payload), self.session
        )
        return web.json_response({"id": todo.id})

    @check_token
    async def patch(self):
        payload = await self.validated_json(UpdateTodo)
        if "done" in payload:
            payload["finish_time"] = func.now()
        todo = await get_item_by_id(Todo, self.todo_id, self.session)
        check_owner(todo, self.token.user_id)
        todo = await update_item(todo, payload, self.session)
        return web.json_response({"id": todo.id})

    @check_token
    async def delete(self):
        todo = await get_item_by_id(Todo, self.todo_id, self.session)
        check_owner(todo, self.token.user_id)
        await delete_item(todo, self.session)
        return web.json_response({"status": "ok"})
