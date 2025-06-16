# In stores/views.py

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied # Import PermissionDenied
from .models import Store
from .serializers import StoreSerializer

class StoreViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stores to be viewed or edited,
    with permission logic handled directly inside the view.
    """
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    # We remove the 'permission_classes' attribute

    def check_permissions(self, request):
        """
        Override the default permission check.
        """
        super().check_permissions(request) # Run default checks first

        # Allow anyone to view the list
        if self.action == 'list':
            return # The check passes

        # For any other action, check the user's role
        if not request.user.role in ['admin', 'store_owner']:
            raise PermissionDenied(detail="You do not have permission to perform this action.")