import logging
from smtplib import SMTPException

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_account_email(subject, message, recipient, from_email=None, **kwargs):
    """Report transport failures so account views can offer a safe retry."""
    try:
        sent = send_mail(subject, message, from_email, [recipient], **kwargs)
    except (SMTPException, OSError) as error:
        # Provider errors can include addresses or credentials; log only their type.
        logger.warning("Account email delivery failed (%s).", type(error).__name__)
        return False

    if sent != 1:
        logger.warning("Account email delivery failed: backend accepted no message.")
        return False
    return True
