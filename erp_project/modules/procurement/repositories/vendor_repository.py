from ..entities.vendor import Vendor

class VendorRepository:

    @staticmethod
    def get_all_active():
        return Vendor.objects.filter(is_active=True)

    @staticmethod
    def get_by_id(vendor_id):
        return Vendor.objects.get(id=vendor_id)

    @staticmethod
    def create(**kwargs):
        return Vendor.objects.create(**kwargs)
