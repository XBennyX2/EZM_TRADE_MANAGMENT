# In transactions/serializers.py
from .models import ReturnRequest

class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = '__all__'
        read_only_fields = ('status', 'requested_by', 'is_item_restocked')