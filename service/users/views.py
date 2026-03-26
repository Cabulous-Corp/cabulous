from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from users.models import User
from users.serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.has_perm("users.add_user"):
            raise PermissionDenied("You do not have permission to create users.")
        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if not self.request.user.has_perm("users.delete_user"):
            raise PermissionDenied("You do not have permission to delete users.")
        instance.delete()
