# Procurement Module

Purchase requests, orders, and suppliers.

## Domain

### Aggregates

**Supplier** (root):
- id, name
- contact_person, email, phone
- address
- is_active

**BudgetCenter** (root):
- id, name, code
- allocated_amount, spent_amount
- year

**PurchaseRequest** (root):
- id, requester_id
- budget_center_id
- description, justification
- estimated_amount, currency
- status (Draft, Submitted, Approved, Rejected)
- requested_at, approved_by, approved_at

**PurchaseOrder** (root):
- id, request_id, supplier_id
- order_number
- items (list)
- total_amount
- status (Draft, Sent, Received, Cancelled)
- ordered_at, received_at

### Value Objects

- `RequestStatus`: Draft, Submitted, Approved, Rejected
- `OrderStatus`: Draft, Sent, Received, Cancelled
- `OrderItem`: product, quantity, unit_price

### Domain Services

- `BudgetChecker`: Verify budget availability
- `ApprovalWorkflow`: Multi-level approval

### Events

- `PurchaseRequested`
- `PurchaseApproved`
- `PurchaseRejected`
- `OrderPlaced`
- `GoodsReceived`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/procurement/suppliers/` | List suppliers |
| POST | `/api/procurement/suppliers/` | Create supplier |
| GET | `/api/procurement/budgets/` | Budget centers |
| GET | `/api/procurement/requests/` | Purchase requests |
| POST | `/api/procurement/requests/` | Create request |
| POST | `/api/procurement/requests/{id}/approve/` | Approve |
| GET | `/api/procurement/orders/` | Purchase orders |
| POST | `/api/procurement/orders/` | Create order |

## Dependencies

- Identity Module (ICurrentUserProvider)
- Accounts Module (for budget integration)
