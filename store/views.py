from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from .models import Store
from .serializers import StoreSerializer

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated] # Base permission for all actions

    def check_permissions(self, request):
        super().check_permissions(request)

        # For writing actions (POST, PUT, DELETE), check for specific roles
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            if not request.user.role in ['admin', 'store_owner']:
                raise PermissionDenied(detail="You do not have permission to manage stores.")