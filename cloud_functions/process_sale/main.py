import os
import json
import pg8000
import sqlalchemy
import functions_framework
import traceback
from google.cloud.sql.connector import Connector, IPTypes
from flask import jsonify, request
from mailjet_rest import Client
import time

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


def write_to_db(product_variant_id, quantity):
    """
    Updates the database with sales information.
    
    Args:
        product_variant_id: The ID of the product variant
        quantity: The quantity purchased
        
    Returns:
        A tuple containing a response and status code
    """
    try:
        pool, connector = connect_with_connector()
        get_sticker_id = sqlalchemy.text(
            f"""
            SELECT sticker_id FROM "public".stickers
            WHERE product_variant_id = '{product_variant_id}'
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
                result = db_conn.execute(get_sticker_id)
                sticker_id_rows = result.fetchall()
                
                if not sticker_id_rows:
                    print(f"No sticker found with product_variant_id: {product_variant_id}")
                    return jsonify({"warning": "No matching sticker found in database"}), 200
                    
                sticker_id = sticker_id_rows[0][0]
                db_conn.execute(update_purchase_count(sticker_id, quantity))
                db_conn.execute(update_user_credits(sticker_id, quantity))
                # commit transaction (SQLAlchemy v2.X.X is commit as you go)
                db_conn.commit()
                return jsonify({"success": "Database updated successfully"}), 200
            except Exception as e:
                print(f"Error updating database: {e}")
                print(traceback.format_exc())
                return jsonify({"error": f"Failed to update database: {str(e)}"}), 500
    finally:
        if 'connector' in locals():
            connector.close()


def send_email(payload):
    """
    Sends an email notification about a new order.
    
    Args:
        payload: The webhook payload containing order details
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Validate payload structure
        if not payload or 'data' not in payload:
            print("Invalid payload structure: missing 'data' field")
            return False
            
        data = payload.get('data', {})
        
        # Extract customer information
        customers = data.get('customers', [])
        if not customers:
            print("No customer information found in payload")
            customer_info = {'email': 'Unknown'}
        else:
            customer_info = customers[0]
            
        # Extract product information
        product_variants = data.get('product_variants', [])
        if not product_variants:
            print("No product information found in payload")
            product_variant = {}
        else:
            product_variant = product_variants[0]
        
        # Extract order details
        customer_email = customer_info.get('email', 'Unknown')
        customer_name = customer_info.get('email', 'Unknown')  # Assuming name isn't available
        product_title = product_variant.get('product_title', 'Unknown Product')
        quantity = product_variant.get('quantity', 1)
        
        # Extract shipping address
        additional_info = product_variant.get('additional_information', [])
        shipping_address = 'No shipping address'
        for info in additional_info:
            if info.get('label') == 'Shipping Address':
                shipping_address = info.get('value', 'No shipping address')
                break
                
        invoice_id = data.get('id', 'Unknown Invoice ID')
        
        # Extract payment status
        status_info = data.get('status', {}).get('status', {})
        payment_status = status_info.get('status', 'Pending') if isinstance(status_info, dict) else 'Pending'
        
        # Extract payment total
        payment_total = data.get('payment', {}).get('total', {}).get('total_usd', '0')
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

        # Check for required environment variables
        required_env_vars = ['MJ_APIKEY_PUBLIC', 'MJ_APIKEY_PRIVATE', 'SENDER_EMAIL', 'SUPPLIER_EMAIL']
        for var in required_env_vars:
            if var not in os.environ:
                print(f"Missing required environment variable: {var}")
                return False

        # Send email using Mailjet API
        api_key = os.environ['MJ_APIKEY_PUBLIC']
        api_secret = os.environ['MJ_APIKEY_PRIVATE']
        mailjet = Client(auth=(api_key, api_secret))

        data = {
            'Messages': [{
                'From': {
                    'Email': os.environ['SENDER_EMAIL'],
                    'Name': 'StickerBot'
                },
                'To': [{
                    'Email': os.environ['SUPPLIER_EMAIL'],
                    'Name': 'Sticker Supplier'
                }],
                'Subject': subject,
                'TextPart': text_part,
                'HTMLPart': html_part
            }]
        }

        result = mailjet.send.create(data=data)
        
        # Check the result and log it
        status_code = result.status_code
        response = result.json()
        
        print(f"Email send status: {status_code}")
        print(f"Email send response: {response}")
        
        if status_code == 200:
            return True
        else:
            print(f"Failed to send email. Status code: {status_code}, Response: {response}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print(traceback.format_exc())
        return False


@functions_framework.http
def process_sale(request):
    """
    Cloud Function to process a sale webhook from sell.app
    """
    try:
        # Log the request details for debugging
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Create a simple test response for debugging
        if request.args.get('test') == 'true':
            return jsonify({"status": "Test successful", "received": "test parameter"}), 200
        
        payload = None
        
        # Try to get JSON data first
        if request.is_json:
            try:
                payload = request.get_json(silent=True)
                print(f"Parsed JSON payload: {payload}")
            except Exception as json_error:
                print(f"Error parsing JSON: {str(json_error)}")
        
        # If no JSON payload, try form data
        if payload is None and request.form:
            form_data = request.form.to_dict()
            print(f"Form data: {form_data}")
            
            if 'payload' in form_data:
                try:
                    payload = json.loads(form_data['payload'])
                    print(f"Parsed payload from form: {payload}")
                except Exception as form_error:
                    print(f"Error parsing form payload: {str(form_error)}")
            else:
                # If there's no payload field but there is form data, use the form data itself
                payload = {"data": form_data}
                print(f"Using form data as payload: {payload}")
        
        # If still no payload, try to parse raw data
        if payload is None and request.data:
            try:
                raw_data = request.data.decode('utf-8')
                print(f"Raw request data: {raw_data}")
                
                # Try to parse as JSON
                try:
                    payload = json.loads(raw_data)
                    print(f"Parsed raw data as JSON: {payload}")
                except:
                    # If not JSON, try to parse as form data
                    if '=' in raw_data:
                        form_items = raw_data.split('&')
                        form_dict = {}
                        for item in form_items:
                            if '=' in item:
                                key, value = item.split('=', 1)
                                form_dict[key] = value
                        
                        payload = {"data": form_dict}
                        print(f"Parsed raw data as form: {payload}")
            except Exception as raw_error:
                print(f"Error processing raw data: {str(raw_error)}")
        
        # If we still don't have a payload, create a minimal one for testing
        if not payload:
            print("No payload found, creating minimal test payload")
            payload = {
                "data": {
                    "id": "test-" + str(int(time.time())),
                    "customers": [{"email": "test@example.com"}],
                    "product_variants": [
                        {
                            "product_title": "Test Product",
                            "product_variant_id": "test-variant",
                            "quantity": 1,
                            "additional_information": [
                                {"label": "Shipping Address", "value": "Test Address"}
                            ]
                        }
                    ],
                    "status": {"status": {"status": "TEST"}}
                }
            }
        
        # Process the webhook data
        email_sent = send_email(payload)
        
        # Extract product info for database update
        try:
            product_variant = payload.get('data', {}).get('product_variants', [])[0]
            product_id = product_variant.get('product_variant_id')
            quantity = product_variant.get('quantity', 1)
            
            if product_id and quantity:
                db_result, status_code = write_to_db(product_id, quantity)
                db_success = status_code == 200
            else:
                print("Missing product_id or quantity in payload")
                db_success = False
                db_result = jsonify({"warning": "Missing product information for database update"})
        except Exception as db_error:
            print(f"Error updating database: {str(db_error)}")
            print(traceback.format_exc())
            db_success = False
            db_result = None
        
        # Prepare response
        response = {
            "success": email_sent or db_success,
            "email_sent": email_sent,
            "db_updated": db_success,
            "payload_received": bool(payload)
        }
        
        if not email_sent and not db_success:
            return jsonify({"error": "Failed to process webhook completely", "details": response}), 500
            
        return jsonify(response), 200
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to process webhook: {str(e)}"}), 500