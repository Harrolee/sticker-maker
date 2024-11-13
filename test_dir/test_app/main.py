# from contextlib import asynccontextmanager
# from dotenv import dotenv_values
from fasthtml.common import *
from app.module_one.rugged import log_hi
log_hi()

# @asynccontextmanager
# async def lifespan(app: FastHTML):
#     # Set up globally accessible singleton objects like db connection pool here
#     config = dotenv_values(dotenv_path="app/.env")
#     app.state.config = StickerConfig(config)
#     # app.state.db_client = DbClient(config)
#     yield
#     # Clean up globally accessible singleton objects here
#     # app.state.db_client.close()

app,rt = fast_app()

@rt('/test-app-import')
def get():
    from test_app.module_one.rugged import log_hi
    return log_hi()


@rt('/app-import')
def get():
    from app.module_one.rugged import log_hi
    return log_hi()

serve()