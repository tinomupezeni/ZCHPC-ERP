"""
Integration tests for the Purchase Request category feature (Slice F11-A):

    - GET /api/v2/procurement/purchase-request-categories/
    - POST /api/v2/procurement/requests/ with category_id per item

Uses the same conftest.py fixtures (requester, outsider, client_for,
category, inactive_category, budget_code) as the rest of this directory.
"""


from rest_framework import status


def _item(**overrides):
    defaults = {
        "description": "USB keyboard",
        "quantity": 2,
        "expected_delivery_period": "Within 2 weeks",
        "estimated_cost": "50.00",
    }
    defaults.update(overrides)
    return defaults


class TestCategoryListEndpoint:
    def test_authorized_requester_receives_only_active_categories(
        self, client_for, category_url, requester, category, inactive_category
    ):
        response = client_for(requester).get(category_url)

        assert response.status_code == status.HTTP_200_OK
        names = [row["name"] for row in response.data]
        assert category.name in names
        assert inactive_category.name not in names

    def test_response_shape_is_id_and_name_only(
        self, client_for, category_url, requester, category
    ):
        response = client_for(requester).get(category_url)

        row = next(r for r in response.data if r["id"] == category.id)
        assert set(row.keys()) == {"id", "name"}
        # The whole point of this endpoint: no AccountChart data leaks.
        assert "account_chart_id" not in row
        assert "code" not in row
        assert "external_account_type" not in row

    def test_anonymous_is_rejected(self, anonymous_client, category_url):
        response = anonymous_client.get(category_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_actor_without_procurement_permission_is_rejected(
        self, client_for, category_url, outsider
    ):
        response = client_for(outsider).get(category_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPurchaseRequestCreationWithCategoryId:
    def test_category_is_persisted_and_budget_code_is_unassigned(
        self, client_for, api_url, requester, category
    ):
        response = client_for(requester).post(
            api_url,
            {"items": [_item(category_id=category.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        item = response.data["items"][0]
        assert item["category_id"] == category.id
        assert item["category"] == {
            "id": category.id,
            "name": category.name,
            "is_active": True,
        }
        # The category's mapped AccountChart must NOT become the budget code.
        assert item["budget_code_id"] is None

    def test_category_is_persisted_in_the_database(
        self, client_for, api_url, requester, category
    ):
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequestItem,
        )

        response = client_for(requester).post(
            api_url,
            {"items": [_item(category_id=category.id)]},
            format="json",
        )

        row = PurchaseRequestItem.objects.get(pk=response.data["items"][0]["id"])
        assert row.category_id == category.id
        assert row.budget_code_id is None

    def test_unknown_category_is_400(self, client_for, api_url, requester):
        response = client_for(requester).post(
            api_url,
            {"items": [_item(category_id=999999)]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "CATEGORY_NOT_FOUND"

    def test_inactive_category_is_400(
        self, client_for, api_url, requester, inactive_category
    ):
        response = client_for(requester).post(
            api_url,
            {"items": [_item(category_id=inactive_category.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "CATEGORY_INACTIVE"

    def test_missing_category_is_400(self, client_for, api_url, requester):
        response = client_for(requester).post(
            api_url,
            {"items": [_item()]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_budget_code_id_alone_is_no_longer_accepted(
        self, client_for, api_url, requester, budget_code
    ):
        """Employees do not own the accounting code, so it is not a valid input."""
        response = client_for(requester).post(
            api_url,
            {"items": [_item(budget_code_id=budget_code.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_supplied_budget_code_id_is_ignored(
        self, client_for, api_url, requester, category, budget_code
    ):
        """An employee cannot smuggle a budget code in next to a category."""
        response = client_for(requester).post(
            api_url,
            {
                "items": [
                    _item(category_id=category.id, budget_code_id=budget_code.id)
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["items"][0]["budget_code_id"] is None

    def test_description_does_not_influence_the_persisted_category(
        self, client_for, api_url, requester, category
    ):
        response = client_for(requester).post(
            api_url,
            {
                "items": [
                    _item(
                        category_id=category.id,
                        description="Totally unrelated text mentioning fuel, travel and advertising",
                    )
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["items"][0]["category_id"] == category.id
