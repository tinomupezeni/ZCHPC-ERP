"""
Workflow Module - Clean Architecture Implementation

Generic declarative approval chains shared by all business modules:

- States, transitions, and structured conditions stored as data
- Resolves which actions an actor may attempt; aggregates and module
  authorization policies keep enforcing on execution

API Endpoints: none directly (consumed via each module's actions endpoint;
pilot: /api/v2/procurement/purchase-requests/<id>/actions/)

Module Structure:
- domain/: Workflow aggregate (entities only, no external dependencies)
- application/: Engine service + repository interface
- infrastructure/: Django models, repository, migrations
- api/: (none - host modules expose the actions endpoints)
- tests/: Engine unit tests
"""
