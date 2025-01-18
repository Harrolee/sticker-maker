import json
import os
from mailjet_rest import Client

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
    print(f"Email send status: {result.status_code}")
    print(f"Email send response: {result.json()}")

data = {
    "event": "order.created",
    "data": {
        "payment": {
            "subtotal": {
                "base": "0",
                "currency": "USD",
                "units": 1,
                "vat": 0,
                "total": {
                    "exclusive": "0",
                    "inclusive": "0"
                }
            },
            "original_amount": {
                "base": "0",
                "currency": "USD",
                "units": 1,
                "vat": 0,
                "total": {
                    "exclusive": "0",
                    "inclusive": "0"
                }
            },
            "total": {
                "exchange_rate": "1",
                "payment_details": {
                    "unit_price": "0",
                    "quantity": 1,
                    "currency": "USD",
                    "modifications": [],
                    "subtotal": "0",
                    "vat": 0,
                    "total": "0",
                    "revenue": "0",
                    "gross_sale": "0"
                },
                "total_usd": "0",
                "revenue_usd": "0",
                "gross_sale_usd": "0"
            },
            "full_price": {
                "base": "0",
                "currency": "USD",
                "units": 1,
                "vat": 0,
                "total": {
                    "exclusive": "0",
                    "inclusive": "0"
                }
            },
            "gateway": {
                "type": None,
                "data": {
                    "checkout_url": "https://sell.app/payment/status/completed/1828810?signature=9f04efab3f6282b922bf4d7aca9ac15ed41efeee896170a2128455151861e040"
                }
            },
            "fee": {
                "base": "0",
                "currency": "USD",
                "units": 1,
                "vat": 0,
                "total": {
                    "exclusive": "0",
                    "inclusive": "0"
                }
            },
            "expires_at": "2024-12-22T17:42:32.000000Z"
        },
        "status": {
            "history": [],
            "status": {
                "status": "PENDING",
                "setAt": "2024-12-21T17:42:32.000000Z",
                "updatedAt": "2024-12-21T17:42:32.000000Z"
            }
        },
        "webhooks": [],
        "feedback": "",
        "id": 1828810,
        "store_id": 51041,
        "coupon_id": None,
        "updated_at": "2024-12-21T17:42:32.000000Z",
        "created_at": "2024-12-21T17:42:32.000000Z",
        "customers": [
            {
                "id": 816427,
                "email": "halzinnia@gmail.com",
                "created_at": "2024-12-21T16:42:59.000000Z",
                "updated_at": "2024-12-21T16:42:59.000000Z",
                "store_id": 51041,
                "visitor_id": 603688,
                "pivot": {
                    "invoice_id": 1828810,
                    "customer_id": 816427,
                    "ip": "73.42.137.63",
                    "country": "United States",
                    "location": "Maple Valley",
                    "proxied": False,
                    "browser_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
                    "vat": {
                        "amount": 0,
                        "country": "US"
                    },
                    "discord_data": None
                }
            }
        ],
        "customer_information": {
            "id": 816427,
            "email": "halzinnia@gmail.com",
            "country": "United States",
            "location": "Maple Valley",
            "ip": "73.42.137.63",
            "proxied": False,
            "browser_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
            "vat": {
                "amount": 0,
                "country": "US"
            }
        },
        "product_variants": [
            {
                "invoice_id": 1828810,
                "product_variant_id": 263950,
                "issue_replacement_invoice_id": None,
                "additional_information": [
                    {
                        "key": "48974cc3df177e6b565c39aa155458cd",
                        "label": "Shipping Address",
                        "value": "cvhj gjkh "
                    }
                ],
                "deliverable": {
                    "types": [
                        "DYNAMIC",
                        "MANUAL"
                    ]
                },
                "quantity": 1,
                "product_title": "Product - 1730242629",
                "variant_title": "Default",
                "invoice_payment": {
                    "total_usd": "0",
                    "revenue_usd": "0",
                    "exchange_rate": "1",
                    "gross_sale_usd": "0",
                    "payment_details": {
                        "vat": 0,
                        "total": "0",
                        "revenue": "0",
                        "currency": "USD",
                        "quantity": 1,
                        "subtotal": "0",
                        "gross_sale": "0",
                        "unit_price": "0",
                        "modifications": []
                    }
                }
            }
        ]
    },
    "store": 51041
}

# Example usage
# payload = json.loads(data)  # You'd get this from your webhook
send_email(data)