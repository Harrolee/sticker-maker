import os
import json
import pg8000
import sqlalchemy
import functions_framework
from google.cloud.sql.connector import Connector, IPTypes
from flask import jsonify
from mailjet_rest import Client

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

def send_email(payload):
    # Extract necessary data from the payload
    customer_info = payload.get('data', {}).get('customers', [])[0]  # Assuming there's always one customer
    product_variant = payload.get('data', {}).get('product_variants', [])[0]
    
    customer_email = customer_info.get('email', 'Unknown')
    customer_name = customer_info.get('email', 'Unknown')  # Assuming name isn't available
    product_title = product_variant.get('product_title', 'Unknown Product')
    quantity = product_variant.get('quantity', 1)
    shipping_address = product_variant.get('additional_information', [{}])[0].get('value', 'No shipping address')
    invoice_id = payload.get('data', {}).get('id', 'Unknown Invoice ID')
    payment_status = payload.get('data', {}).get('status', {}).get('status', {}).get('status', 'Pending')
    payment_total = payload.get('data', {}).get('payment', {}).get('total', {}).get('total_usd', '0')
    product_variant_id = product_variant.get('product_variant_id', 'Unknown Variant ID')

    # Prepare the subject and body for the email
    subject = f"Sticker Order - {invoice_id} - {payment_status}"
    text_part = (
        f"Customer Email: {customer_email}\n"
        f"Customer Name: {customer_name}\n"
        f"Product Title: {product_title}\n"
        f"Product Variant ID: {product_variant_id}\n"
        f"Quantity: {quantity}\n"
        f"Shipping Address: {shipping_address}\n"
        f"Invoice ID: {invoice_id}\n"
        f"Payment Status: {payment_status}\n"
        f"Payment Total: {payment_total} USD\n"
    )
        # f"Link to Payment: https://sell.app/payment/status/completed/{invoice_id}?signature=9f04efab3f6282b922bf4d7aca9ac15ed41efeee896170a2128455151861e040"

    html_part = f"""
    <h3>Sticker Order Details</h3>
    <p><strong>Customer Email:</strong> {customer_email}</p>
    <p><strong>Customer Name:</strong> {customer_name}</p>
    <p><strong>Product Title:</strong> {product_title}</p>
    <p><strong>Product Variant ID:</strong> {product_variant_id}</p>
    <p><strong>Quantity:</strong> {quantity}</p>
    <p><strong>Shipping Address:</strong> {shipping_address}</p>
    <p><strong>Invoice ID:</strong> {invoice_id}</p>
    <p><strong>Payment Status:</strong> {payment_status}</p>
    <p><strong>Payment Total:</strong> {payment_total} USD</p>
    """
    # <p><a href="https://sell.app/payment/status/completed/{invoice_id}?signature=9f04efab3f6282b922bf4d7aca9ac15ed41efeee896170a2128455151861e040">View Payment Status</a></p>

    # Send email using Mailjet API
    api_key = os.environ['MJ_APIKEY_PUBLIC']
    api_secret = os.environ['MJ_APIKEY_PRIVATE']
    mailjet = Client(auth=(api_key, api_secret))

    data = {
        'FromEmail': os.environ['SENDER_EMAIL'],
        'FromName': 'StickerBot',
        'Subject': subject,
        'Text-part': text_part,
        'Html-part': html_part,
        'Recipients': [{'Email': os.environ['SUPPLIER_EMAIL']}]
    }

    result = mailjet.send.create(data=data)
    
    # Check the result and log it
    print(result.status_code)
    print(result.json())

# Example usage
payload = json.loads('your_payload_here')  # You'd get this from your webhook
send_email(payload)


@functions_framework.http
def process_sale(request):
    print(request)
    print(request.form.to_dict())
    # if request.content_type != 'application/x-www-form-urlencoded':
    #     return jsonify({"error": "Unsupported Content-Type"}), 400

    # result = write_to_db(gumroad_product_id, quantity)
    send_email()
    # consider edge cases
    return 200