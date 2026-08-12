import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Gmail SMTP Configuration from environment variables
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "eventnov22@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body_html, body_text=None, notification_type="Account Update", user_id=None):
        """
        Sends an automatic email via Gmail SMTP.
        Logs delivery status to MongoDB EmailNotificationLogs collection.
        If email sending fails, logs error gracefully without raising exception.
        """
        if not to_email or "@" not in to_email:
            error_msg = f"Invalid destination email address: {to_email}"
            logger.error(error_msg)
            EmailService._log_email_status(user_id, to_email, notification_type, "Failed", error_msg)
            return False, error_msg

        if not MAIL_PASSWORD:
            error_msg = "Gmail App Password (MAIL_PASSWORD) is not configured in backend/.env"
            logger.warning(error_msg)
            EmailService._log_email_status(user_id, to_email, notification_type, "Failed", error_msg)
            return False, error_msg

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Secure Morse Comm Administrator <{MAIL_USERNAME}>"
        msg["To"] = to_email

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as server:
                if MAIL_USE_TLS:
                    server.starttls()
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.sendmail(MAIL_USERNAME, [to_email], msg.as_string())
                
            logger.info(f"Successfully sent {notification_type} email to {to_email}")
            EmailService._log_email_status(user_id, to_email, notification_type, "Sent", None)
            return True, "Email notification delivered successfully."
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            EmailService._log_email_status(user_id, to_email, notification_type, "Failed", error_msg)
            return False, f"Account status updated successfully, but notification email could not be delivered: {error_msg}"

    @classmethod
    def send_approval_email(cls, recipient_email, username, user_id=None):
        """
        Sends account approval email to the user's Gmail address.
        """
        subject = "Secure Morse Communication — Account Approved"
        html_content = f"""
        <div style="font-family: 'Courier New', monospace; background-color: #040d1a; color: #e6f1ff; padding: 25px; border-radius: 10px; border: 1px solid #00ff66;">
            <h2 style="color: #00ff66; margin-top: 0;">CYBER DEFENSE MATRIX // ACCOUNT APPROVED</h2>
            <p>Greetings <strong>{username}</strong>,</p>
            <p>Your registration request for access to the <strong>Secure Morse Communication System</strong> has been officially <span style="color: #00ff66; font-weight: bold;">APPROVED</span> by the System Administrator.</p>
            <div style="background: rgba(0, 255, 102, 0.1); border-left: 4px solid #00ff66; padding: 12px; margin: 20px 0;">
                <p style="margin: 0; font-weight: bold;">Next Authentication Steps:</p>
                <ol style="margin-top: 8px; margin-bottom: 0;">
                    <li>Navigate to the Login Portal.</li>
                    <li>Enter your Username and Password.</li>
                    <li>Complete the mandatory <strong>Biometric Face Verification</strong> step using your camera.</li>
                    <li>Upon successful face verification, access will be granted to the Secure Communication Terminal.</li>
                </ol>
            </div>
            <p style="color: #8892b0; font-size: 12px;">This is an automated security notification. Please do not reply directly to this email.</p>
        </div>
        """
        text_content = f"Greetings {username},\nYour account has been APPROVED. You can now log in using your Username, Password, and Biometric Face Verification."
        return cls.send_email(recipient_email, subject, html_content, text_content, "Approval Notification", user_id)

    @classmethod
    def send_rejection_email(cls, recipient_email, username, user_id=None):
        """
        Sends account rejection email to the user's Gmail address.
        """
        subject = "Secure Morse Communication — Account Registration Update"
        html_content = f"""
        <div style="font-family: 'Courier New', monospace; background-color: #040d1a; color: #e6f1ff; padding: 25px; border-radius: 10px; border: 1px solid #ff0055;">
            <h2 style="color: #ff0055; margin-top: 0;">CYBER DEFENSE MATRIX // REGISTRATION UPDATE</h2>
            <p>Greetings <strong>{username}</strong>,</p>
            <p>Your registration request for access to the <strong>Secure Morse Communication System</strong> was <span style="color: #ff0055; font-weight: bold;">NOT APPROVED</span> by the System Administrator at this time.</p>
            <p>Terminal clearance is currently restricted. If you believe this is in error, please contact your security organization administrator.</p>
            <p style="color: #8892b0; font-size: 12px;">This is an automated security notification.</p>
        </div>
        """
        text_content = f"Greetings {username},\nYour registration request for the Secure Morse Communication System was not approved."
        return cls.send_email(recipient_email, subject, html_content, text_content, "Rejection Notification", user_id)

    @staticmethod
    def _log_email_status(user_id, recipient_email, notification_type, status, error_message=None):
        try:
            from app.models.email_log import EmailNotificationLogModel
            EmailNotificationLogModel.log_notification(
                user_id=str(user_id) if user_id else "Unknown",
                recipient_email=recipient_email,
                notification_type=notification_type,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to log email notification status: {e}")
