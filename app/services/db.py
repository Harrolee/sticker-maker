from sqlalchemy import create_engine
from sqlalchemy.sql import text

from make_sticker.config import StickerConfig

config = StickerConfig()


engine = create_engine(config.db_connection_string)


def db_connection():
    with engine.connect() as conn:
        stmt = text("select * from postgres")
        print(conn.execute(stmt).fetchall())


if __name__ == "__main__":
    db_connection()