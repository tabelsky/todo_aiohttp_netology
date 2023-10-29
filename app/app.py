from aiohttp import web

from context import init_db
from middleware import http_errors_middleware, session_middleware
from views import LoginView, TodoView, UserView


def _get_app() -> web.Application:
    app = web.Application()
    app.middlewares.extend([http_errors_middleware, session_middleware])
    app.cleanup_ctx.append(init_db)

    app.add_routes(
        [
            web.post("/login", LoginView),
            web.get("/user", UserView),
            web.post("/user", UserView),
            web.patch("/user", UserView),
            web.delete("/user", UserView),
            web.get("/todo", TodoView),
            web.get("/todo/{todo_id:\d+}", TodoView),
            web.post("/todo", TodoView),
            web.patch("/todo/{todo_id:\d+}", TodoView),
            web.delete("/todo/{todo_id:\d+}", TodoView),
        ]
    )

    return app


async def get_app():
    return _get_app()


if __name__ == "__main__":
    web.run_app(_get_app())
