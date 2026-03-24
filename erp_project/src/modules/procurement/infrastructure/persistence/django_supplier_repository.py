"""
Django repository implementation for Supplier.
"""

from decimal import Decimal
from typing import List, Optional

from modules.procurement.infrastructure.persistence.models import Vendor as VendorModel

from modules.procurement.domain.entities import Supplier
from modules.procurement.application.interfaces import ISupplierRepository


class DjangoSupplierRepository(ISupplierRepository):
    """Django implementation of supplier repository."""

    def _to_domain(self, model: VendorModel) -> Supplier:
        """Convert Django model to domain entity."""
        return Supplier(
            id=model.id,
            name=model.name,
            email=model.email,
            phone=model.phone,
            address=model.address,
            rating=Decimal(str(model.rating)),
            is_active=model.is_active,
        )

    def _to_model(self, entity: Supplier) -> VendorModel:
        """Convert domain entity to Django model."""
        if entity.id:
            model = VendorModel.objects.get(pk=entity.id)
        else:
            model = VendorModel()

        model.name = entity.name
        model.email = entity.email
        model.phone = entity.phone
        model.address = entity.address
        model.rating = entity.rating
        model.is_active = entity.is_active
        return model

    def save(self, supplier: Supplier) -> Supplier:
        """Save a supplier."""
        model = self._to_model(supplier)
        model.save()
        return self._to_domain(model)

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Get a supplier by ID."""
        try:
            model = VendorModel.objects.get(pk=supplier_id)
            return self._to_domain(model)
        except VendorModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[Supplier]:
        """Get all suppliers."""
        if include_inactive:
            queryset = VendorModel.objects.all()
        else:
            queryset = VendorModel.objects.filter(is_active=True)
        return [self._to_domain(m) for m in queryset]

    def get_active(self) -> List[Supplier]:
        """Get active suppliers."""
        return self.get_all(include_inactive=False)

    def search(self, query: str) -> List[Supplier]:
        """Search suppliers by name."""
        queryset = VendorModel.objects.filter(
            name__icontains=query,
            is_active=True
        )
        return [self._to_domain(m) for m in queryset]

    def delete(self, supplier_id: int) -> bool:
        """Delete a supplier."""
        try:
            model = VendorModel.objects.get(pk=supplier_id)
            model.delete()
            return True
        except VendorModel.DoesNotExist:
            return False
