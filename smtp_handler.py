import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("smtp-handler")


class EmailHandler:
    """Handle email notifications via SMTP."""
    
    def __init__(self, email: str, password: str, server: str, port: int):
        self.email = email
        self.password = password
        self.server = server
        self.port = port
    
    def send_confirmation(self, to_email: str, product: str, amount: float, order_id: int) -> bool:
        """Send purchase confirmation email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = f"Order #{order_id} Confirmation"
            
            body = f"""
Thank you for your purchase!

Product: {product}
Amount: ${amount:.2f}
Order ID: {order_id}

Your credentials will be delivered shortly.

Do not share this order ID publicly.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Confirmation sent to {to_email}")
            return True
        except Exception as exc:
            logger.exception("Failed to send email: %s", exc)
            return False
    
    def send_credentials(self, to_email: str, product: str, credentials: str) -> bool:
        """Send database credentials."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = f"Your {product} Credentials"
            
            body = f"""
Your {product} credentials:

{credentials}

Keep these safe. Do not share them.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Credentials sent to {to_email}")
            return True
        except Exception as exc:
            logger.exception("Failed to send credentials: %s", exc)
            return False
