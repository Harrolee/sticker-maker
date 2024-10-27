import os
import json
import pg8000
import sqlalchemy
import functions_framework
from google.cloud.sql.connector import Connector, IPTypes
from flask import jsonify

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """

    instance_connection_name = os.environ[
        "INSTANCE_CONNECTION_NAME"
    ]
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # lazy cuz cloud function
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


def write_to_db(gumroad_product_id, quantity):
    pool, connector = connect_with_connector()
    get_sticker_id = lambda gumroad_product_id: sqlalchemy.text(
        f"""
        SELECT sticker_id FROM "public".stickers
        WHERE gumroad_product_id = '{gumroad_product_id}'
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

    response = ''
    with pool.connect() as db_conn:
        try:
            sticker_id = db_conn.execute(get_sticker_id(gumroad_product_id)).fetchall()
            sticker_id = sticker_id[0][0]
            db_conn.execute(update_purchase_count(sticker_id, quantity))
            db_conn.execute(update_user_credits(sticker_id, quantity))
            # commit transaction (SQLAlchemy v2.X.X is commit as you go)
            db_conn.commit()
            response = jsonify({"Hype": "Data inserted successfully."}), 200
        except Exception as e:
            print(f"Error inserting data: {e}")
            response = jsonify({"error": "Failed to update database"}), 500
        finally:
            connector.close()
            return response


@functions_framework.http
def process_sale(request):
    if request.content_type != 'application/x-www-form-urlencoded':
        return jsonify({"error": "Unsupported Content-Type"}), 400
    try:
        quantity = request.form.get('quantity')
        gumroad_product_id = request.form.get('product_id')
    except (KeyError, TypeError, json.JSONDecodeError):
        return jsonify({"error": "Invalid request; 'quantity' and 'gumroad_product_id' are required."}), 400    
    return write_to_db(gumroad_product_id, quantity)