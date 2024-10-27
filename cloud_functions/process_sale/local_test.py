import os
import json
import functions_framework
from google.cloud.sql.connector import Connector
from flask import jsonify

# Initialize the Cloud SQL Connector
connector = Connector(refresh_strategy="lazy") # lazy because we are in a cloud function

# Create a connection function
def getconn():
    conn = connector.connect(
        os.environ["INSTANCE_CONNECTION_NAME"],
        "pg8000",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        db=os.environ["DB_NAME"],
    )
    return conn

def write_to_db(gumroad_product_id, quantity):
# increment user's credits by 1 per quantity

# given a gumroad_product_id
    # find the sticker-maker product
    # increment purchaseCount for that sticker

    # find the user connect to that product
    # increment their credits value
    print(f'first OPeningDB connection')
    conn = getconn()
    print(f'got connections')

    try:
        print(f'OPeningDB connection')
        # Open a new database connection
        with getconn() as conn:
            print(f'in with construct')
            with conn.cursor() as cursor:
                print(f'using a cursor and about to get sticker_Id')
                sticker_id = cursor.execute(
                    f"""
                    SELECT sticker_id 
                    FROM "public".stickers
                    WHERE gumroad_product_id == {gumroad_product_id}
                    """
                )
                print(f'first query results: {sticker_id}')
                update_purchase_count = cursor.execute(
                    f"""
                    UPDATE sticker
                    SET sales = sales + 1
                    WHERE sticker_id = {gumroad_product_id};
                    """
                )
                print(f'update purchase results: {update_purchase_count}')
                update_credit_results = cursor.execute(
                    f"""
                    UPDATE users
                    SET credits = credits + 1
                    WHERE userId = (SELECT creator FROM sticker WHERE sticker_id = {sticker_id});
                    """
                )
                print(f'update credit results: {update_credit_results}')
                conn.commit()
        return jsonify({"messproduct_name": "Data inserted successfully."}), 200
    except Exception as e:
        print(f"Error inserting data: {e}")
        return jsonify({"error": "Failed to insert data into the database."}), 500
    finally:
        connector.close()