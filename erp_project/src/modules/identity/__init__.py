"""
Identity Module

Handles user management, authentication, and authorization.

Public interfaces:
- IIdentityProvider: For other modules to authenticate/authorize
- ICurrentUserProvider: For getting current user context

Key entities:
- User: System user with authentication
- Role: Permission grouping
- AuditLogEntry: Security audit trail
"""
