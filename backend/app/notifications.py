import smtplib
from email.message import EmailMessage
from .config import settings

class NotificationService:
    def send_email(self, to, subject, body):
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(msg)
            return {"status": "sent", "channel": "email", "to": to}
        except Exception as exc:
            return {"status": "failed", "channel": "email", "to": to, "error": str(exc)}

    def send_approval_request(self, approval_id, investigation_id, action, risk):
        link = f"{settings.app_base_url}/approvals?approval={approval_id}"
        body = (
            "AIOps Guardian Pro requires approval.\n\n"
            f"Investigation: {investigation_id}\nAction: {action}\nRisk: {risk}\n\n"
            f"Review and approve using the authenticated portal:\n{link}\n\n"
            "Do not approve operational changes by replying to this email.\n"
        )
        return self.send_email(settings.approval_email_to, f"[AIOps Guardian] Approval required: {action}", body)

notifications = NotificationService()
