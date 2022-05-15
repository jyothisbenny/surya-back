from rest_framework import mixins
from rest_framework.viewsets import ViewSetMixin as DRF_ViewSetMixin

from ..api import generics, views


class ViewSetMixin(DRF_ViewSetMixin):
    """
    Overrides the `check_permissions` method to provide `action` keyword
    """

    def check_action_permissions(self, request, action=None, obj=None):
        if action is None:
            action = self.action
        return super(ViewSetMixin, self).check_action_permissions(request, action=action, obj=obj)


class ViewSet(ViewSetMixin, views.APIView):
    """
    The base ViewSet class does not provide any actions by default.
    """
    pass


class GenericViewSet(ViewSetMixin, generics.GenericAPIView):
    """
    The GenericViewSet class does not provide any actions by default,
    but does include the base set of generic view behavior, such as
    the `get_object` and `get_queryset` methods.
    """

    def initial(self, request, *args, **kwargs):
        """
        Runs anything that needs to occur prior to calling the method handler.
        """
        super(GenericViewSet, self).initial(request, *args, **kwargs)

        # Check action permissions
        self.check_action_permissions(request)


class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
