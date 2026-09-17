import os
import logging
import email.policy
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import EmailOTP

logger = logging.getLogger(__name__)


class InlineImageEmailMessage(EmailMultiAlternatives):
    """
    Subclass of EmailMultiAlternatives that packages inline CID images
    into a standard RFC 2387 multipart/related body attached to the HTML alternative,
    ensuring email clients like Gmail, Apple Mail, and Outlook render the images
    directly in the email body rather than showing them as generic downloadable attachments.
    """
    def __init__(self, *args, **kwargs):
        self.inline_images = []
        super().__init__(*args, **kwargs)

    def attach_inline_image(self, content_bytes, maintype, subtype, cid, filename='image.png'):
        self.inline_images.append({
            'bytes': content_bytes,
            'maintype': maintype,
            'subtype': subtype,
            'cid': cid.strip('<>'),
            'filename': filename
        })

    def message(self, *, policy=None):
        use_policy = policy if policy is not None else email.policy.default
        msg = super().message(policy=use_policy)
        if self.inline_images:
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    for img in self.inline_images:
                        part.add_related(
                            img['bytes'],
                            maintype=img['maintype'],
                            subtype=img['subtype'],
                            cid=f"<{img['cid']}>",
                            filename=img['filename'],
                            disposition='inline'
                        )
                    break
        return msg


def send_otp_email(email, purpose='signup'):
    """
    Generates a secure 6-digit OTP and dispatches a branded HTML email to the user with the official K9Match logo.
    Supports 'signup' and 'forgot_password'.
    Returns (success: bool, otp_obj: EmailOTP, error_message: str|None).
    """
    try:
        otp_obj = EmailOTP.generate_otp(email=email, purpose=purpose, validity_minutes=10)
        
        if purpose == 'signup':
            subject = f"{otp_obj.otp_code} is your K9Match Verification Code"
        else:
            subject = f"{otp_obj.otp_code} is your K9Match Password Reset Code"

        # Load official logo for inline CID rendering
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'logo.png')
        logo_bytes = None
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_bytes = f.read()

        context = {
            'email': email,
            'otp_code': otp_obj.otp_code,
            'purpose': purpose,
            'subject': subject,
        }

        html_content = render_to_string('emails/otp_email.html', context)
        text_content = (
            f"Your K9Match verification code is: {otp_obj.otp_code}\n\n"
            f"This code will expire in 10 minutes.\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"— The K9Match Team"
        )

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not from_email:
            host_user = getattr(settings, 'EMAIL_HOST_USER', '')
            from_email = f"K9Match <{host_user}>" if host_user else 'K9Match <no-reply@k9match.com>'

        msg = InlineImageEmailMessage(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[email]
        )
        msg.attach_alternative(html_content, "text/html")

        if logo_bytes:
            msg.attach_inline_image(logo_bytes, 'image', 'png', 'k9match_logo', 'logo.png')

        msg.send(fail_silently=False)

        return True, otp_obj, None

    except Exception as e:
        logger.exception("Failed to send OTP email to %s: %s", email, str(e))
        return False, None, str(e)
