import pytest
from sqlalchemy import create_engine

from config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from models import Base

from .api_client import TodoApiClient
from .config import API_HOST
from .constants import (
    DEFAULT_USER_NAME,
    DEFAULT_USER_PASSWORD,
    NEW_TODO_ITEM_IMPORTANT,
    NEW_TODO_ITEM_NOT_IMPORTANT,
    NEW_USER_NAME,
    NEW_USER_NAME_WITH_TODOS,
)


@pytest.fixture(scope="session", autouse=True)
def init_db():
    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture()
def client():
    return TodoApiClient(API_HOST)


@pytest.fixture(scope="session")
def default_user_client() -> TodoApiClient:
    client = TodoApiClient(API_HOST)
    client.create_user(DEFAULT_USER_NAME, DEFAULT_USER_PASSWORD)
    client.auth(DEFAULT_USER_NAME, DEFAULT_USER_PASSWORD)
    return client


@pytest.fixture()
def new_user_client(client) -> TodoApiClient:
    client.create_user(NEW_USER_NAME, DEFAULT_USER_PASSWORD)
    client.auth(NEW_USER_NAME, DEFAULT_USER_PASSWORD)
    yield client
    client.delete_user()


@pytest.fixture()
def new_user_client_with_todos(client) -> TodoApiClient:
    client.create_user(NEW_USER_NAME_WITH_TODOS, DEFAULT_USER_PASSWORD)
    client.auth(NEW_USER_NAME_WITH_TODOS, DEFAULT_USER_PASSWORD)
    client.create_todo(NEW_TODO_ITEM_IMPORTANT, important=True)
    client.create_todo(NEW_TODO_ITEM_NOT_IMPORTANT, important=False)
    yield client
    client.delete_user()


@pytest.fixture()
def client_non_authorized(client) -> TodoApiClient:
    client.headers["token"] = "wrong_token"
    return client
