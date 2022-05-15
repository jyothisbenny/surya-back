from rest_framework import viewsets
from django.contrib.auth import logout, get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action

from .filters import UserBasicFilter
from .models import User
from .serializers import UserSerializer, UserBasicDataSerializer
from .services import auth_login, auth_register_user, auth_password_change
from ..base import response
from ..base.serializers import SawaggerResponseSerializer
from ..base.api.pagination import StandardResultsSetPagination


class UserViewSet(viewsets.ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = None

    def get_queryset(self):
        queryset = super(UserViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = UserBasicFilter
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        method="post",
        operation_summary='Login',
        operation_description='Post login credential to log in and get a login session token.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="mobile/email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description=""),
            }),
        responses={
            200: SawaggerResponseSerializer(data={'message': 'Logged In'}, partial=True)
        }
    )
    @action(detail=False, methods=['POST'])
    def login(self, request):
        return auth_login(request)

    @action(detail=False, methods=['POST'])
    def logout(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
            logout(request)
        return response.Ok({"detail": "Successfully logged out."})

    @action(detail=False, methods=['POST'])
    def register(self, request):
        data = auth_register_user(request)
        return response.Created(data)

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def users_list(self, request):
        queryset = User.objects.filter(is_active=True, is_separated=False, is_superuser=False,
                                                   is_staff=False)
        queryset = queryset.order_by('first_name', 'last_name')
        self.filterset_class = UserBasicFilter
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(UserBasicDataSerializer(page, many=True).data)
        return response.Ok(UserBasicDataSerializer(queryset, many=True).data)

    @swagger_auto_schema(
        method="post",
        operation_summary='Change Password',
        operation_description='Post old and new password while logged in session.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description=""),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description=""),
            }),
        responses={
            200: SawaggerResponseSerializer(data={'message': 'Password changed Successfully.'}, partial=True)
        }
    )
    @action(detail=False, methods=['POST'])
    def password_change(self, request):
        data = auth_password_change(request)
        user, new_password = request.user, data.get('new_password')
        if new_password:
            if len(new_password) < 6:
                return response.BadRequest({"detail": "Password too short."})
        if user.check_password(data.get('old_password')):
            user.set_password(new_password)
            user.save()
            content = {'success': 'Password changed successfully.'}
            return response.Ok(content)
        else:
            content = {'detail': 'Old password is incorrect.'}
            return response.BadRequest(content)

    @action(detail=False, methods=['POST'])
    def superadmin_password_reset(self, request):
        data = request.data.copy()
        print("--------------------", data)
        user_id = data.get('user', None)
        password = data.get('password', None)
        if user_id:
            user = get_user_model().objects.filter(pk=user_id).first()
            if user:
                if password:
                    if len(password) < 8:
                        return response.BadRequest({"detail": "Password Length too short."})
                    user.set_password(password)
                    user.save()
                    content = {'success': 'Password changed successfully.'}
                    return response.Ok(content)
                return response.BadRequest({"detail": "Password is Null."})
            return response.BadRequest({"detail": "User Doesn't exist."})
        return response.BadRequest({"detail": "User is required."})
