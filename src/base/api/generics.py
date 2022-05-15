from rest_framework import generics as DRF_generics
from rest_framework import exceptions


class GenericAPIView(DRF_generics.GenericAPIView):
    def get_object(self):
        obj = super(GenericAPIView, self).get_object()
        self.check_action_permissions(self.request, self.action, obj)
        return obj

    def check_action_permissions(self, request, action, obj=None):
        """
        Check if the request should be permitted for specified actions
        Raises an appropriate exception if the request is not permitted.
        """
        if action is None:
            self.permission_denied(request)

        for permission in self.get_permissions():
            if not permission.has_action_permission(request, self, action, obj):
                self.permission_denied(request)


class PlutonicGenericAPIView(GenericAPIView):
    def app_permission_denied(self, request, message=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if not request.successful_authenticator and not message:
            raise exceptions.NotAuthenticated()
        if message:
            raise exceptions.PermissionDenied(detail=message)
        raise exceptions.PermissionDenied(detail=message)
