"""
Procurement Module - Clean Architecture Implementation

This module provides procurement functionality including:
- Supplier management
- Inventory item management
- Budget center management
- Purchase request workflow with multi-level approval
- Purchase order lifecycle management

API Endpoints: /api/v2/procurement/

Module Structure:
- domain/: Domain layer (entities, value objects, events, services)
- application/: Application layer (services, DTOs, interfaces)
- infrastructure/: Infrastructure layer (Django repositories)
- api/: API layer (views, serializers, URLs)

For backwards compatibility, legacy endpoints at /api/procurement/
are still available but deprecated.
"""
