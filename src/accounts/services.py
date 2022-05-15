import random, re
import string
from collections import namedtuple
from functools import partial

from django.contrib.auth import get_user_model
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from .serializers import LoginSerializer, UserSerializer, UserRegistrationSerializer, PasswordChangeSerializer
from ..base import response

User = namedtuple('User', ['email', 'password'])


def _parse_data(data, cls):
    """
    Generic function for parse user data using
    specified validator on `cls` keyword parameter.
    Raises: ValidationError exception if
    some errors found when data is validated.
    Returns the validated data.
    """
    serializer = cls(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer.validated_data


# Parse Auth login data
parse_auth_login_data = partial(_parse_data, cls=LoginSerializer)
parse_auth_password_change_data = partial(_parse_data, cls=PasswordChangeSerializer)
parse_register_user_data = partial(_parse_data, cls=UserRegistrationSerializer)


def auth_login(request):
    """
    params: request
    return: token, password
    """
    data, auth_data = parse_auth_login_data(request.data), None
    username, password = data.get('username'), data.get('password')
    if username and password:
        user, email_user, mobile_user = get_user_from_email_or_mobile(username)
        if not user:
            return response.BadRequest({'detail': 'User does not exists.'})
        if user.is_separated:
            return response.BadRequest({'detail': 'User has been separated'})
        if user.check_password(password):
            if not user.is_active:
                return response.BadRequest({'detail': 'User account is disabled.'})
            auth_data = generate_auth_data(request, user)
            return response.Ok(auth_data)
        else:
            if mobile_user:
                return response.BadRequest({'detail': 'Incorrect Mobile Number and password.'})
            else:
                return response.BadRequest({'detail': 'Incorrect Email and Password.'})
    else:
        return response.BadRequest({'detail': 'Must Include username and password.'})


def auth_register_user(request):
    """
    params: request
    return: user
    """
    user_model = get_user_model()
    data = parse_register_user_data(request.data)
    user_data = User(
        email=data.get('email'),
        password=data.get('password')
    )
    user = None
    # Check email is register as a active user
    try:
        user = get_user_model().objects.get(email=data.get('email'), is_active=True)
    except get_user_model().DoesNotExist:
        pass
    # if user is not exist, create a Inactive user
    if not user:
        un_active_user = user_model.objects.filter(email=user_data.email, is_active=False)
        if un_active_user:
            user_model.objects.filter(email=user_data.email, is_active=False).delete()
        user = user_model.objects.create_user(**dict(data), is_active=True)
    user_obj = user_model.objects.filter(email=data.get('email')).first()
    if user_obj:
        user_obj.set_password(data.get('password'))
        user_obj.save()
    return UserRegistrationSerializer(user).data


def get_user_from_email_or_mobile(username):
    user_model = get_user_model()
    mobile_user = user_model.objects.filter(mobile=username).first()
    email_user = user_model.objects.filter(email=username).first()
    if email_user:
        user = email_user
    else:
        user = mobile_user
    return user, email_user, mobile_user


def generate_auth_data(request, user):
    token, created = Token.objects.get_or_create(user=user)
    login(request, user)
    auth_data = {
        "token": token.key,
        "user": UserSerializer(instance=user, context={'request': request}).data
    }
    return auth_data


def auth_password_change(request):
    """
    params: request
    return: data
    """
    data = parse_auth_password_change_data(request.data)
    return data
