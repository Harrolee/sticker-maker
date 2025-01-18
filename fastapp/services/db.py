from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine, text
import os

class DbClient():
    def __init__(self):
        self.is_local = os.environ.get('IS_LOCAL', 'false').lower() == 'true'
        self._setup_connection()
        self.queries = self.Queries()

    def _setup_connection(self):
        if self.is_local:
            print("Setting up local database connection...")
            self.db_user = 'postgres'
            self.db_name = 'postgres'
            self.db_pass = 'postgres'
            self.db_host = 'db' if os.environ.get('DOCKER_ENV') else 'localhost'
            self.engine = create_engine(
                f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"
            )
            print("Local database connection established")
        else:
            print("Setting up cloud database connection...")
            self.db_user = os.environ.get('DB_USER')
            self.db_name = os.environ.get('DB_NAME')
            self.db_pass = os.environ.get('DB_PASS')
            self.instance_connection_name = os.environ.get('INSTANCE_CONNECTION_NAME')
            self.engine, self.connector = self._cloud_sql_connect()

    def _cloud_sql_connect(self):
        connector = Connector(refresh_strategy="lazy")
        
        def getconn():
            return connector.connect(
                self.instance_connection_name,
                "pg8000",
                user=self.db_user,
                password=self.db_pass,
                db=self.db_name,
            )

        engine = create_engine("postgresql+pg8000://", creator=getconn)
        return engine, connector

    def close(self):
        if hasattr(self, 'connector'):
            try:
                self.connector.close()
            except Exception as e:
                print(f"Error closing Cloud SQL connector: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    class Queries():
        def create_user(self, name, email):
            return text(
                """
                INSERT INTO users (name, email, credits)
                VALUES (:name, :email, 0)
                RETURNING user_id
                """
            ).bindparams(name=name, email=email)

        def save_sticker(self, storefront_product_id, sticker_name, creator_id):
            return text(
                """
                INSERT INTO stickers (storefront_product_id, name, sales, creator)
                VALUES (:product_id, :name, 0, :creator_id)
                """
            ).bindparams(
                product_id=storefront_product_id,
                name=sticker_name,
                creator_id=creator_id
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
                print("about to unpack")
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

if __name__ == "__main__":
    with DbClient() as client:
        # client.create_user('dojacat', 'd@kitty.com')
        print(client.all_users())