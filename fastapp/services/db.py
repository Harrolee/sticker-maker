from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql import text
import pg8000

class DbClient():
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if hasattr(self, 'connector') and self.connector:
            try:
                self.connector.close()
            except Exception as e:
                print(f"Error closing Cloud SQL connector: {e}")

    def __init__(self, config):
        self.is_local = config["IS_LOCAL"]
        if self.is_local == 'true':
            self.db_user = 'postgres'
            self.db_name = 'postgres'
            self.db_pass = 'postgres'
            self.db_host = 'localhost'
            self.db_connection_string = f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"
            self.engine = create_engine(self.db_connection_string)
        else:
            self.db_user = config["DB_USER"]
            self.db_name = config["DB_NAME"]
            self.db_pass = config["DB_PASS"]
            self.instance_connection_name = config["INSTANCE_CONNECTION_NAME"]
            self.engine, self.connector = self.cloud_sql_connect_with_connector()
        self.queries = self.Queries()

    class Queries():
        def create_user(self, name, email):
            return text(
               f"""
                    INSERT INTO users (name, email, credits)
                    VALUES ('{name}', '{email}', 0)
                    RETURNING user_id
                """
            )

        def save_sticker(self, storefront_product_id, sticker_name, creator_id):
            return text(
                f"""
                    INSERT INTO stickers (storefront_product_id, name, sales, creator)
                    VALUES ({storefront_product_id}, '{sticker_name}', 0, {creator_id})
                """
                )

    def db_connection(self):
        with self.engine.connect() as conn:
            stmt = text("select * from postgres")
            print(conn.execute(stmt).fetchall())

    def create_user(self, name, email):
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(self.queries.create_user(name, email))
                    user_id = result.scalar()  # Fetch the generated user_id
                return user_id
        except Exception as e:
                print(f"Error creating user: {e}")

    def all_users(self) -> int | None:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM users"))
                results = result.all()
            return results
        except Exception as e:
                    print(f"Error getting users: {e}")

    def find_user_by_email(self, email) -> tuple | None:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT user_id, name FROM users WHERE email = :email"), {"email": email})
                user_id, name = result.first()
            return user_id, name
        except Exception as e:
                    print(f"Error getting user info: {e}")

    def save_sticker(self, storefront_product_id, sticker_name, creator_id):
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(self.queries.save_sticker(storefront_product_id, sticker_name, creator_id))
        except Exception as e:
                    print(f"Error saving sticker: {e}")

    def cloud_sql_connect_with_connector(self) -> Engine:
        """
        Initializes a connection pool for a Cloud SQL instance of Postgres.

        Uses the Cloud SQL Python Connector package.
        """

        # initialize Cloud SQL Python Connector object
        connector = Connector(refresh_strategy="lazy")

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.dbapi.Connection = connector.connect(
                self.instance_connection_name,
                "pg8000",
                user=self.db_user,
                password=self.db_pass,
                db=self.db_name,
            )
            return conn

        pool = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        return pool, connector

if __name__ == "__main__":
    with DbClient() as client:
        # client.create_user('dojacat', 'd@kitty.com')
        print(client.all_users())