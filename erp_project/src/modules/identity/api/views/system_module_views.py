from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from modules.identity.infrastructure.persistence.models import SystemModule
from modules.identity.api.serializers.system_module_serializers import SystemModuleSerializer

class SystemModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing System Modules.
    """
    queryset = SystemModule.objects.all()
    serializer_class = SystemModuleSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'identifier'

    @action(detail=True, methods=['post'])
    def install(self, request, identifier=None):
        module = self.get_object()
        module.is_active = True
        module.save()
        return Response(self.get_serializer(module).data)

    @action(detail=True, methods=['post'])
    def uninstall(self, request, identifier=None):
        module = self.get_object()
        module.is_active = False
        module.save()
        return Response(self.get_serializer(module).data)

    @action(detail=False, methods=['get'], url_path='active')
    def active_modules(self, request):
        active_modules = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_modules, many=True)
        return Response(serializer.data)
