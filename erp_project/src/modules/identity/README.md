# Identity Module

User management, authentication, and authorization.

## Domain

### Entities

- **User** (aggregate root): id, email, hashed_password, first_name, last_name, is_active, is_staff, failed_attempts, lockout_until
- **Role**: id, name, display_name, permissions
- **AuditLogEntry**: user_id, event_type, ip_address, timestamp, details

### Value Objects

- `HashedPassword`: Securely stored password
- `RoleName`: Validated role name
- `Permission`: Single permission string

### Domain Services

- `PasswordHasher`: Hash and verify passwords
- `LockoutPolicy`: Handle failed login attempts

### Events

- `UserCreated`
- `UserLocked`
- `UserUnlocked`
- `LoginSucceeded`
- `LoginFailed`

## Interfaces Exposed

```python
class IIdentityService(Protocol):
    def authenticate(self, email: str, password: str) -> AuthResult: ...
    def get_user(self, user_id: UUID) -> UserDTO: ...
    def check_permission(self, user_id: UUID, permission: str) -> bool: ...

class ICurrentUserProvider(Protocol):
    def get_current_user(self) -> UserDTO: ...
    def get_current_permissions(self) -> list[str]: ...
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token/` | Obtain JWT token |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |
| GET | `/api/auth/users/` | List users |
| POST | `/api/auth/users/` | Create user |
| GET | `/api/auth/users/{id}/` | Get user |
| PUT | `/api/auth/users/{id}/` | Update user |
| GET | `/api/auth/roles/` | List roles |
| GET | `/api/auth/logs/` | Audit logs |

## Dependencies

None (foundational module)
