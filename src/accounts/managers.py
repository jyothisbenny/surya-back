import binascii
import os

from django.conf import settings
from django.contrib.auth.models import BaseUserManager
from django.core import signing
from django.db import models
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.utils import timezone


def _generate_code():
    return binascii.hexlify(os.urandom(20))


class UserManager(BaseUserManager):

    def _create_user(self, email, password,
                     is_active, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Email must be set for the user')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_active=is_active,
                          is_staff=is_staff,
                          is_superuser=is_superuser,
                          last_login=now,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        is_active = extra_fields.pop("is_active", False)
        return self._create_user(email, password, is_active=is_active, is_staff=False, is_superuser=False,
                                 **extra_fields)

    def create_superuser(self, email, password):
        return self._create_user(email, password, is_active=True, is_staff=True, is_superuser=True)


class PasswordResetCodeManager(models.Manager):

    def create_reset_code(self, user):
        """
        Create the password reset code for non-registered user who comes first time to `clinic.bkarogyam.com`.
        Create  Django's cryptographic signing API to generate one-time secret URLs for password resets
        """
        password_reset_code = self.filter(user=user).order_by("-created_at")
        if password_reset_code:
            password_reset_code = password_reset_code[0]
            time = password_reset_code.modified_at
            modtime = timezone.localtime(time)
            increase_now = timezone.now()
            diff_in_time = (increase_now - modtime)
            diff_in_min = diff_in_time.seconds
            if diff_in_min <= settings.PASSWORD_SESSION_EXPIRE:
                self.update(modified_at=timezone.now())
                return password_reset_code
            signer = signing.TimestampSigner()
            var = signer.sign(user.password)
            var = var.split(':')
            timestamp = var[1]
            signature = var[2]
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            code = _generate_code()
            password_reset_code = self.create(user=user, code=code, uid=uid, timestamp=timestamp, signature=signature)
            return password_reset_code

        signer = signing.TimestampSigner()
        var = signer.sign(user.password)
        var = var.split(':')
        timestamp = var[1]
        signature = var[2]
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        code = _generate_code()
        password_reset_code = self.create(user=user, code=code, uid=uid, timestamp=timestamp, signature=signature)
        return password_reset_code
