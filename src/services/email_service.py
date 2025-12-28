"""Email service for sending emails"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        """Initialize email service"""
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'SMTP_FROM_EMAIL', self.smtp_username)
        self.from_name = getattr(settings, 'SMTP_FROM_NAME', 'AI Caller')
        self.enabled = getattr(settings, 'EMAIL_ENABLED', False)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("email_disabled", to_email=to_email, subject=subject)
            return False

        if not self.smtp_username or not self.smtp_password:
            logger.warning("email_config_missing", to_email=to_email)
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info("email_sent", to_email=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("email_send_failed", error=str(e), to_email=to_email)
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url: Optional custom reset URL (if not provided, uses default format)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not reset_url:
            # Default reset URL format
            base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            reset_url = f"{base_url}/reset-password?token={reset_token}"

        subject = "Password Reset Request"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #2563eb;">Password Reset Request</h2>
              <p>You requested to reset your password for your AI Caller account.</p>
              <p>Click the button below to reset your password:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                  Reset Password
                </a>
              </div>
              <p style="font-size: 12px; color: #666;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_url}">{reset_url}</a>
              </p>
              <p style="font-size: 12px; color: #666;">
                This link will expire in 1 hour. If you didn't request this, please ignore this email.
              </p>
            </div>
          </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        You requested to reset your password for your AI Caller account.
        
        Click the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour. If you didn't request this, please ignore this email.
        """

        return self.send_email(to_email, subject, html_body, text_body)


# Global email service instance
email_service = EmailService()

