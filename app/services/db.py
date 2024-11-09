from sqlalchemy import create_engine
from sqlalchemy.sql import text

from make_sticker.config import StickerConfig

config = StickerConfig()


engine = create_engine(config.db_connection_string)


def db_connection():
    with engine.connect() as conn:
        stmt = text("select * from postgres")
        print(conn.execute(stmt).fetchall())


def save_sticker(storefront_product_id, sticker_name, creator_id):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO stickers (storefront_product_id, name, sales, creator)
                VALUES (:storefront_product_id, :sticker_name, 0, :creator_id)
            """),
            {"storefront_product_id": storefront_product_id, "sticker_name": sticker_name, "creator_id": creator_id}
        )

if __name__ == "__main__":
    db_connection()