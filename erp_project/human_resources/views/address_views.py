# addresses/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..hr_models import Address
from ..serializers.address_serializer import AddressSerializer
from ..services import address_services

class AddressViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing addresses.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create method to use the service layer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call the service
        address = address_services.create_address(serializer.validated_data)
        
        headers = self.get_success_headers(serializer.data)
        return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Overrides the default update method (PUT) to use the service layer.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        address = address_services.update_address(instance, serializer.validated_data)
        return Response(AddressSerializer(address).data)

    def partial_update(self, request, *args, **kwargs):
        """
        Overrides the default partial_update (PATCH) to use the service layer.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        address = address_services.update_address(instance, serializer.validated_data)
        return Response(AddressSerializer(address).data)

    def destroy(self, request, *args, **kwargs):
        """
        Overrides the default destroy (DELETE) to use the service layer.
        """
        instance = self.get_object()
        address_services.delete_address(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)