"""
OpenAPI Documentation Configuration

This module provides configuration for API documentation generation.
Install drf-spectacular to use these settings:

    pip install drf-spectacular

Then add to INSTALLED_APPS:
    'drf_spectacular',

And add to urls.py:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns = [
        path('api/v2/docs/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/v2/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]
"""

# Add to settings.py when drf-spectacular is installed:
SPECTACULAR_SETTINGS = {
    'TITLE': 'ZCHPC ERP API',
    'DESCRIPTION': '''
# ZCHPC ERP System API

Welcome to the ZCHPC ERP API documentation. This API provides access to all
ERP functionality including HR, Payroll, Accounting, Procurement, and more.

## API Versioning

This documentation covers the **v2 API** endpoints, which follow clean
architecture principles. Legacy v1 endpoints are deprecated and will be
removed in a future version.

## Authentication

All endpoints (except public ones) require JWT authentication.

```
Authorization: Bearer <access_token>
```

To obtain a token, use the login endpoint:
- Employee Portal: POST `/api/v2/portal/auth/login/`
- Admin/Staff: POST `/api/v2/auth/login/`

## Modules

| Module | Description |
|--------|-------------|
| **Identity** | User management, authentication |
| **HR** | Employees, departments, positions |
| **Attendance** | Clock in/out, QR tokens |
| **Leave** | Leave requests, balances |
| **Recruitment** | Jobs, candidates, applications |
| **Payroll** | Payslips, salary processing |
| **Accounts** | Financial accounting, journals |
| **Procurement** | Purchase requests, orders |
| **Portal** | Employee self-service |

## Response Format

All responses follow a consistent JSON format:

```json
{
    "data": { ... },
    "message": "Success",
    "errors": null
}
```

## Error Handling

Errors return appropriate HTTP status codes:
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error
    ''',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # API organization
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Employees', 'description': 'Employee management'},
        {'name': 'Departments', 'description': 'Department management'},
        {'name': 'Positions', 'description': 'Position/job title management'},
        {'name': 'Attendance', 'description': 'Time tracking and QR clock-in'},
        {'name': 'Leave', 'description': 'Leave requests and balances'},
        {'name': 'Recruitment', 'description': 'Job postings and applications'},
        {'name': 'Payroll', 'description': 'Salary processing and payslips'},
        {'name': 'Accounts', 'description': 'Financial accounting'},
        {'name': 'Procurement', 'description': 'Purchase management'},
        {'name': 'Portal', 'description': 'Employee self-service portal'},
    ],

    # Security schemes
    'SECURITY': [{'BearerAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },

    # Swagger UI settings
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
    },

    # Schema customization
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,

    # Enum handling
    'ENUM_NAME_OVERRIDES': {
        'ExpenseStatusEnum': 'modules.portal.domain.value_objects.ExpenseStatus',
        'LeaveStatusEnum': 'modules.leave.domain.value_objects.LeaveStatus',
        'PayslipStatusEnum': 'modules.payroll.domain.value_objects.PayslipStatus',
    },

    # Contact and license
    'CONTACT': {
        'name': 'ZCHPC IT Department',
        'email': 'it@zchpc.co.zw',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },

    # Server URLs
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
        {'url': 'https://api.zchpc.co.zw', 'description': 'Production server'},
    ],
}


# REST Framework settings to add for schema generation
REST_FRAMEWORK_SCHEMA_SETTINGS = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
