import logging

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _


from ..base.models import TimeStampedModel
from .managers import UserManager, PasswordResetCodeManager


# Sending Email
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


# Create your models here.


class User(AbstractBaseUser, TimeStampedModel):
    first_name = models.CharField(max_length=128, blank=True, null=True, default='')
    last_name = models.CharField(max_length=128, blank=True, null=True, default='')
    mobile = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    address = models.CharField(max_length=1024, null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_separated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    # Email address to be used as the username
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name_plural = 'Users'

    def __str__(self):
        """Returns the email of the User when it is printed in the console"""
        return self.email

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = self.first_name
        if self.last_name:
            full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name or ''


class AbstractBaseCode(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="User_Abstract", on_delete=models.PROTECT)
    code = models.CharField(_('code'), max_length=524, primary_key=True)
    uid = models.CharField(max_length=40, default='uidrequired')
    timestamp = models.CharField(max_length=40, default='timestamprequired')
    signature = models.CharField(max_length=60, default='signaturerequired')

    class Meta:
        abstract = True

    def send_email(self):
        subject = "Reset Your Password"
        text_content = """Reset your password by clicking on this link:
                      %s{{ uid }}/{{ timestamp }}/{{ signature }}/{{  code }}
        """ % (settings.PASSWORD_RESET_URL)
        # subject = render_to_string(subject_file).strip()
        from_email = settings.DEFAULT_EMAIL_FROM
        to = self.user.email
        # bcc_email = settings.DEFAULT_EMAIL_BCC
        # Make some context available
        ctxt = {
            'url': settings.PASSWORD_RESET_URL,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': (self.code).decode(),
            'uid': self.uid,
            'timestamp': self.timestamp,
            'signature': self.signature

        }
        # text_content = render_to_string(txt_file, ctxt)
        html_content = render_to_string('email/password_reset.html', ctxt)
        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, 'text/html')
            msg.send()
            print("Email Sent successfully")
        except Exception:
            logger.exception("Unable to send the mail.")

    def __unicode__(self):
        return "{0}, {1}, {2}, {3}".format(self.code, self.uid, self.timestamp, self.signature)


class PasswordResetCode(AbstractBaseCode):
    code = models.CharField(max_length=255, primary_key=True)
    objects = PasswordResetCodeManager()

    def send_password_reset_email(self):
        self.send_email()

