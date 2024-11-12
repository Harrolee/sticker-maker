from contextlib import asynccontextmanager
from dotenv import dotenv_values
from fasthtml.common import *
from app.make_sticker.config import StickerConfig
from app.services.db import DbClient

@asynccontextmanager
async def lifespan(app: FastHTML):
    # Set up globally accessible singleton objects like db connection pool here
    config = dotenv_values(dotenv_path="app/.env")
    app.state.config = StickerConfig(config)
    app.state.db_client = DbClient(config)
    yield
    # Clean up globally accessible singleton objects here
    app.state.db_client.close()

app,rt = fast_app()

@rt('/dot-relative-import')
def get():
    from .make_sticker.config import StickerConfig
    config = StickerConfig()
    from .module_one.rugged import log_hi
    return log_hi()


@rt('/relative-import')
def get():
    from module_one.rugged import log_hi
    return log_hi()


@rt('/absolute-import')
def get():
    from app.module_one.rugged import log_hi
    return log_hi()

serve()