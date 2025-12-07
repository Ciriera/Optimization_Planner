"""
Email sending service for instructor notifications.
Uses SMTP to send HTML emails.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        # Flexible SMTP settings - supports Gmail, Outlook, Yahoo, and other providers
        # Common SMTP servers:
        # - Gmail: smtp.gmail.com (port 587)
        # - Outlook/Hotmail: smtp-mail.outlook.com (port 587)
        # - Yahoo: smtp.mail.yahoo.com (port 587)
        # - Custom: Set SMTP_HOST and SMTP_PORT in environment variables
        self.smtp_host = settings.SMTP_HOST or "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_user = settings.SMTP_USER or ""  # Your email address
        self.smtp_password = settings.SMTP_PASSWORD or ""  # Your email password or App Password
        self.smtp_tls = settings.SMTP_TLS if settings.SMTP_TLS is not None else True
        self.from_email = settings.EMAILS_FROM_EMAIL or self.smtp_user
        self.from_name = settings.EMAILS_FROM_NAME or "Optimization Planner System"
        
        # Validate configuration
        if not self.smtp_password:
            logger.warning("SMTP_PASSWORD is not set. Email sending will fail. Please set SMTP_PASSWORD in environment variables.")
        if not self.smtp_user:
            logger.warning("SMTP_USER is not set. Please set your email address in SMTP_USER environment variable.")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Tuple[bytes, str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional, auto-generated from HTML if not provided)
            
        Returns:
            Dict with 'success' (bool) and 'error' (str if failed)
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Create text version if not provided
            if not text_content:
                # Simple HTML to text conversion (basic)
                import re
                text_content = re.sub(r"<[^>]+>", "", html_content)
                text_content = text_content.replace("&nbsp;", " ")
                text_content = text_content.strip()
            
            # Add both text and HTML parts
            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Add attachments if provided
            # attachments format: [(bytes, filename, content_type), ...]
            if attachments:
                for attachment_data, filename, content_type in attachments:
                    if content_type.startswith('image/'):
                        img = MIMEImage(attachment_data)
                        # Use attachment disposition for downloadable files
                        # Check if filename contains "full_resolution" or "attachment" to determine if it should be downloadable
                        if 'full_resolution' in filename.lower() or 'attachment' in filename.lower():
                            img.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            logger.info(f"Added image attachment: {filename} ({len(attachment_data)} bytes)")
                        else:
                            # Use inline for images that should be displayed in email body
                            img.add_header('Content-Disposition', 'inline', filename=filename)
                            img.add_header('Content-ID', f'<{filename}>')
                            logger.info(f"Added inline image attachment: {filename} ({len(attachment_data)} bytes), Content-ID: <{filename}>")
                        msg.attach(img)
                    else:
                        from email.mime.base import MIMEBase
                        from email import encoders
                        part = MIMEBase(*content_type.split('/', 1))
                        part.set_payload(attachment_data)
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)
                        logger.info(f"Added attachment: {filename} ({len(attachment_data)} bytes)")
            
            # Validate password before attempting connection
            if not self.smtp_password:
                error_msg = "SMTP_PASSWORD is not configured. Please set SMTP_PASSWORD environment variable with your email password or App Password."
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Connect to SMTP server and send
            try:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                server.set_debuglevel(0)  # Set to 1 for debug output (disabled for security)
                
                if self.smtp_tls:
                    server.starttls()
                
                # Login with credentials
                server.login(self.smtp_user, self.smtp_password)
                
                # Send message
                server.send_message(msg)
                server.quit()
                
            except smtplib.SMTPAuthenticationError as e:
                # Provide helpful error messages based on email provider
                error_str = str(e).lower()
                provider_hint = ""
                
                if "gmail.com" in self.smtp_host.lower():
                    provider_hint = " For Gmail: Use your regular password if 2FA is disabled, or use App Password if 2FA is enabled (https://myaccount.google.com/apppasswords)."
                elif "outlook.com" in self.smtp_host.lower() or "hotmail.com" in self.smtp_host.lower():
                    if "basic authentication is disabled" in error_str or "authentication unsuccessful" in error_str:
                        provider_hint = " Outlook/Hotmail no longer supports basic authentication. Please switch to Gmail (smtp.gmail.com) or use OAuth2. For Gmail: Set SMTP_HOST=smtp.gmail.com and use App Password."
                    else:
                        provider_hint = " For Outlook/Hotmail: Modern accounts require OAuth2. Consider using Gmail instead (smtp.gmail.com) with App Password."
                elif "yahoo.com" in self.smtp_host.lower():
                    provider_hint = " For Yahoo: Use your regular password or generate an App Password from your Yahoo account settings."
                else:
                    provider_hint = " Please check your email and password. Some providers may require App Passwords if 2FA is enabled."
                
                error_msg = f"SMTP Authentication failed. Please check your email and password.{provider_hint} Error: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            except smtplib.SMTPException as e:
                error_msg = f"SMTP error: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True, "error": None}
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def send_test_email(self, admin_email: str = None) -> Dict[str, Any]:
        """
        Send a test email to admin address.
        
        Args:
            admin_email: Admin email address (defaults to SMTP_USER if not provided)
            
        Returns:
            Dict with 'success' and 'error'
        """
        if not admin_email:
            admin_email = self.smtp_user or "test@example.com"
        
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email from Optimization Planner</h2>
            <p>This is a test email to verify email configuration.</p>
            <p>If you received this email, the email service is working correctly.</p>
            <p><strong>Sent at:</strong> {timestamp}</p>
            <p><strong>From:</strong> {from_email}</p>
        </body>
        </html>
        """.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            from_email=self.from_email
        )
        
        return self.send_email(
            to_email=admin_email,
            subject="Test Email - Optimization Planner",
            html_content=html_content,
        )

