from rest_framework import exceptions
from rest_framework.views import APIView as DRF_APIView


class APIView(DRF_APIView):
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


class BuildMapAPIView(APIView):

    def app_permission_denied(self, request, message=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if not request.successful_authenticator and not message:
            raise exceptions.NotAuthenticated()
        if message:
            raise exceptions.PermissionDenied(detail=message)
        raise exceptions.PermissionDenied(detail=message)
