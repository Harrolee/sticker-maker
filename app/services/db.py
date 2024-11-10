from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ..make_sticker.config import StickerConfig

config = StickerConfig()


engine = create_engine(config.db_connection_string)


def db_connection():
    with engine.connect() as conn:
        stmt = text("select * from postgres")
        print(conn.execute(stmt).fetchall())


def create_user(name, email):
    with engine.connect() as conn:
        with conn.begin():
            result = conn.execute(
                text("""
                    INSERT INTO users (name, email, credits)
                    VALUES (:name, :email, 0)
                    RETURNING user_id
                """),
                {"name": name, "email": email}
            )
            user_id = result.scalar()  # Fetch the generated user_id
    return user_id

def all_users() -> int | None:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users"),
        )
        results = result.all()
    return results

def find_user_info_by_email(email) -> tuple | None:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT user_id, name FROM users WHERE email = :email"),
            {"email": email}
        )
        user_id, name = result.first()
    return user_id, name


def user_in_db(user_id):
    # select user by user_id

    # if not in db, add user to db
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO users (name, email, credits)
                VALUES (:storefront_product_id, :sticker_name, 0, :creator_id)
            """),
            {"storefront_product_id": storefront_product_id, "sticker_name": sticker_name, "creator_id": creator_id}
        )

    # return true if the above works
    return True

def save_sticker(storefront_product_id, sticker_name, creator_id):
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                text("""
                    INSERT INTO stickers (storefront_product_id, name, sales, creator)
                    VALUES (:storefront_product_id, :sticker_name, 0, :creator_id)
                """),
                {"storefront_product_id": storefront_product_id, "sticker_name": sticker_name, "creator_id": creator_id}
            )

if __name__ == "__main__":
    db_connection()