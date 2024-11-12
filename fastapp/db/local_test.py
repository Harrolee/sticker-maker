import os
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
import sqlalchemy
from dotenv import load_dotenv
load_dotenv()

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """

    instance_connection_name = os.environ[
        "INSTANCE_CONNECTION_NAME"
    ]  # e.g. 'project:region:instance'
    db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector(refresh_strategy="lazy")

    def getconn() -> pg8000.dbapi.Connection:
        conn: pg8000.dbapi.Connection = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=ip_type,
        )
        return conn

    # The Cloud SQL Python Connector can be used with SQLAlchemy
    # using the 'creator' argument to 'create_engine'
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool, connector

def write_to_db(storefront_product_id, quantity):
    pool, connector = connect_with_connector()
    get_sticker_id = lambda storefront_product_id: sqlalchemy.text(
        f"""
        SELECT sticker_id FROM "public".stickers
        WHERE gumroad_product_id = '{storefront_product_id}'
        """
    )
    update_purchase_count = lambda sticker_id, quantity: sqlalchemy.text(
        f"""
        UPDATE "public".stickers
        SET sales = sales + {quantity}
        WHERE sticker_id = '{sticker_id}';
        """
    )
    update_user_credits = lambda sticker_id, quantity: sqlalchemy.text(
        f"""
        UPDATE "public".users
        SET credits = credits + {quantity}
        WHERE user_id = (SELECT creator FROM stickers WHERE sticker_id = {sticker_id});
        """
    )

    with pool.connect() as db_conn:
        try:
            sticker_id = db_conn.execute(get_sticker_id(storefront_product_id)).fetchall()
            sticker_id = sticker_id[0][0]
            db_conn.execute(update_purchase_count(sticker_id, quantity))
            db_conn.execute(update_user_credits(sticker_id, quantity))
            # commit transaction (SQLAlchemy v2.X.X is commit as you go)
            db_conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            connector.close()


