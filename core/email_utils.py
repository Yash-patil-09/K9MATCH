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


def _get_logo_bytes():
    """Loads official logo for inline CID rendering."""
    logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                return f.read()
        except Exception:
            pass
    return None


def _get_from_email():
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not from_email:
        host_user = getattr(settings, 'EMAIL_HOST_USER', '')
        from_email = f"K9Match <{host_user}>" if host_user else 'K9Match <no-reply@k9match.com>'
    return from_email


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

        logo_bytes = _get_logo_bytes()

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

        from_email = _get_from_email()

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


def send_match_proposal_email(match_request, request=None):
    """
    Dispatches a transactional email to the target canine's owner when a breeding proposal is sent.
    """
    try:
        recipient = match_request.receiver
        if not recipient or not recipient.email:
            return False, "Recipient has no email address"

        sender_user = match_request.sender
        sender_dog = match_request.sender_dog
        target_dog = match_request.target_dog

        from django.urls import reverse
        rel_url = reverse('match_requests_dashboard')
        action_url = request.build_absolute_uri(rel_url) if request else f"https://k9match.com{rel_url}"

        subject = f"🐾 New Breeding Match Proposal for {target_dog.name} from {sender_user.username}"

        context = {
            'recipient_name': recipient.first_name or recipient.username,
            'sender_username': sender_user.username,
            'sender_dog_name': sender_dog.name if sender_dog else None,
            'sender_dog_breed': sender_dog.breed if sender_dog else None,
            'sender_dog_city': sender_dog.city if sender_dog else None,
            'target_dog_name': target_dog.name,
            'proposal_message': match_request.message,
            'action_url': action_url,
            'subject': subject,
        }

        html_content = render_to_string('emails/match_proposal_email.html', context)
        text_content = (
            f"Hello {recipient.username},\n\n"
            f"{sender_user.username} has sent a breeding match proposal for {target_dog.name}!\n"
            f"{'Proposing canine: ' + sender_dog.name if sender_dog else ''}\n"
            f"{'Note: ' + match_request.message if match_request.message else ''}\n\n"
            f"Review and respond to this proposal here: {action_url}\n\n"
            f"— The K9Match Team"
        )

        msg = InlineImageEmailMessage(
            subject=subject,
            body=text_content,
            from_email=_get_from_email(),
            to=[recipient.email]
        )
        msg.attach_alternative(html_content, "text/html")

        logo_bytes = _get_logo_bytes()
        if logo_bytes:
            msg.attach_inline_image(logo_bytes, 'image', 'png', 'k9match_logo', 'logo.png')

        msg.send(fail_silently=False)
        return True, None

    except Exception as e:
        logger.exception("Failed to send match proposal email for match %s: %s", getattr(match_request, 'id', None), str(e))
        return False, str(e)


def send_match_accepted_email(match_request, request=None):
    """
    Dispatches a celebratory email to the proposing user when their match proposal is accepted.
    """
    try:
        recipient = match_request.sender
        if not recipient or not recipient.email:
            return False, "Recipient has no email address"

        partner_user = match_request.receiver
        sender_dog = match_request.sender_dog
        target_dog = match_request.target_dog

        from django.urls import reverse
        rel_url = reverse('chat_room', args=[match_request.id])
        chat_url = request.build_absolute_uri(rel_url) if request else f"https://k9match.com{rel_url}"

        subject = f"🎉 Great News! Match Proposal Accepted for {target_dog.name}"

        context = {
            'recipient_name': recipient.first_name or recipient.username,
            'partner_username': partner_user.username,
            'sender_dog_name': sender_dog.name if sender_dog else 'Your canine',
            'target_dog_name': target_dog.name,
            'chat_url': chat_url,
            'subject': subject,
        }

        html_content = render_to_string('emails/match_accepted_email.html', context)
        text_content = (
            f"Congratulations {recipient.username}!\n\n"
            f"{partner_user.username} has accepted your breeding match proposal between "
            f"{sender_dog.name if sender_dog else 'your canine'} and {target_dog.name}.\n\n"
            f"You can now chat directly to coordinate details: {chat_url}\n\n"
            f"— The K9Match Team"
        )

        msg = InlineImageEmailMessage(
            subject=subject,
            body=text_content,
            from_email=_get_from_email(),
            to=[recipient.email]
        )
        msg.attach_alternative(html_content, "text/html")

        logo_bytes = _get_logo_bytes()
        if logo_bytes:
            msg.attach_inline_image(logo_bytes, 'image', 'png', 'k9match_logo', 'logo.png')

        msg.send(fail_silently=False)
        return True, None

    except Exception as e:
        logger.exception("Failed to send match accepted email for match %s: %s", getattr(match_request, 'id', None), str(e))
        return False, str(e)


def send_match_declined_email(match_request, request=None):
    """
    Dispatches a polite update to the proposing user when their match proposal is declined.
    """
    try:
        recipient = match_request.sender
        if not recipient or not recipient.email:
            return False, "Recipient has no email address"

        partner_user = match_request.receiver
        target_dog = match_request.target_dog

        from django.urls import reverse
        rel_url = reverse('explore_dogs')
        explore_url = request.build_absolute_uri(rel_url) if request else f"https://k9match.com{rel_url}"

        subject = f"Update on your Match Proposal for {target_dog.name}"

        context = {
            'recipient_name': recipient.first_name or recipient.username,
            'partner_username': partner_user.username,
            'target_dog_name': target_dog.name,
            'explore_url': explore_url,
            'subject': subject,
        }

        html_content = render_to_string('emails/match_declined_email.html', context)
        text_content = (
            f"Hello {recipient.username},\n\n"
            f"{partner_user.username} was unable to accept your breeding match proposal for {target_dog.name} at this time.\n\n"
            f"You can explore more available canines here: {explore_url}\n\n"
            f"— The K9Match Team"
        )

        msg = InlineImageEmailMessage(
            subject=subject,
            body=text_content,
            from_email=_get_from_email(),
            to=[recipient.email]
        )
        msg.attach_alternative(html_content, "text/html")

        logo_bytes = _get_logo_bytes()
        if logo_bytes:
            msg.attach_inline_image(logo_bytes, 'image', 'png', 'k9match_logo', 'logo.png')

        msg.send(fail_silently=False)
        return True, None

    except Exception as e:
        logger.exception("Failed to send match declined email for match %s: %s", getattr(match_request, 'id', None), str(e))
        return False, str(e)

