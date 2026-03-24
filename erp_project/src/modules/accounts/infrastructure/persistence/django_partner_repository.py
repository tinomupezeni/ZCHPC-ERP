"""
Django implementation of partner repository.
"""

from typing import List, Optional

from modules.accounts.infrastructure.persistence.models import Partner as PartnerModel
from modules.accounts.domain.entities import Partner
from modules.accounts.domain.value_objects import PartnerType
from modules.accounts.application.interfaces import IPartnerRepository


class DjangoPartnerRepository(IPartnerRepository):
    """Django ORM implementation of partner repository."""

    TYPE_TO_DOMAIN = {
        "customer": PartnerType.CUSTOMER,
        "supplier": PartnerType.SUPPLIER,
        "employee": PartnerType.EMPLOYEE,
    }

    TYPE_TO_MODEL = {
        PartnerType.CUSTOMER: "customer",
        PartnerType.SUPPLIER: "supplier",
        PartnerType.EMPLOYEE: "employee",
    }

    def _to_domain(self, model: PartnerModel) -> Partner:
        """Convert Django model to domain entity."""
        partner_type = self.TYPE_TO_DOMAIN.get(
            model.partner_type,
            PartnerType.CUSTOMER
        )

        return Partner(
            id=model.id,
            name=model.name,
            partner_type=partner_type,
            vat_number=model.vat_number,
            currency_id=model.currency_id,
            email=None,  # Legacy model doesn't have these
            phone=None,
            address=None,
            is_active=True,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model_data(self, partner: Partner) -> dict:
        """Convert domain entity to model data."""
        partner_type = self.TYPE_TO_MODEL.get(
            partner.partner_type,
            "customer"
        )

        return {
            "name": partner.name,
            "partner_type": partner_type,
            "vat_number": partner.vat_number,
            "currency_id": partner.currency_id,
        }

    def save(self, partner: Partner) -> Partner:
        """Save a partner."""
        data = self._to_model_data(partner)

        if partner.id is None:
            model = PartnerModel.objects.create(**data)
        else:
            PartnerModel.objects.filter(id=partner.id).update(**data)
            model = PartnerModel.objects.get(id=partner.id)

        return self._to_domain(model)

    def get_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get a partner by ID."""
        try:
            model = PartnerModel.objects.get(id=partner_id)
            return self._to_domain(model)
        except PartnerModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[Partner]:
        """Get all partners."""
        models = PartnerModel.objects.all().order_by("name")
        return [self._to_domain(m) for m in models]

    def get_by_type(
        self,
        partner_type: PartnerType,
        include_inactive: bool = False
    ) -> List[Partner]:
        """Get partners by type."""
        model_type = self.TYPE_TO_MODEL.get(partner_type, "customer")
        models = PartnerModel.objects.filter(
            partner_type=model_type
        ).order_by("name")
        return [self._to_domain(m) for m in models]

    def get_customers(self, include_inactive: bool = False) -> List[Partner]:
        """Get all customers."""
        return self.get_by_type(PartnerType.CUSTOMER, include_inactive)

    def get_suppliers(self, include_inactive: bool = False) -> List[Partner]:
        """Get all suppliers."""
        return self.get_by_type(PartnerType.SUPPLIER, include_inactive)

    def search(self, query: str) -> List[Partner]:
        """Search partners by name."""
        models = PartnerModel.objects.filter(
            name__icontains=query
        ).order_by("name")[:50]
        return [self._to_domain(m) for m in models]

    def delete(self, partner_id: int) -> bool:
        """Delete a partner."""
        deleted, _ = PartnerModel.objects.filter(id=partner_id).delete()
        return deleted > 0
