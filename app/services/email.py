import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.make_sticker.config import StickerConfig
from app.services.models import OrderInfo


def send_email(order: OrderInfo, config: StickerConfig):
    # Email content
    body = order.pretty_print()

    # Setting up the message
    msg = MIMEMultipart()
    msg["From"] = config.sender_email
    msg["To"] = config.supplier_email # DR games
    msg["Subject"] = f"New Order - {order.order_id}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        server.starttls()  # Enable security
        server.login(config.sender_email, config.sender_email_password)
        server.sendmail(config.sender_email, config.supplier_email, msg.as_string())
