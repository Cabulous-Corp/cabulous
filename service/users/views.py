from rest_framework.viewsets import ModelViewSet

from users.models import User
from users.permissions import UserModelPermissions
from users.serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [UserModelPermissions]
