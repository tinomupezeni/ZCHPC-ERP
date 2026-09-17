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
    def test_category_resolves_to_the_correct_budget_code_id(
        self, client_for, api_url, requester, category
    ):
        response = client_for(requester).post(
            api_url,
            {"items": [_item(category_id=category.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["items"][0]["budget_code_id"] == category.account_chart_id

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

    def test_missing_category_and_budget_code_is_400(
        self, client_for, api_url, requester
    ):
        response = client_for(requester).post(
            api_url,
            {"items": [_item()]},  # neither category_id nor budget_code_id
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_supplying_both_category_id_and_budget_code_id_is_400(
        self, client_for, api_url, requester, category, budget_code
    ):
        """
        The employee must not be able to choose an arbitrary AccountChart ID
        by also supplying budget_code_id alongside a category_id - this is
        rejected outright rather than silently picking a winner.
        """
        response = client_for(requester).post(
            api_url,
            {
                "items": [
                    _item(category_id=category.id, budget_code_id=budget_code.id)
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_raw_budget_code_id_still_works_unchanged(
        self, client_for, api_url, requester, budget_code
    ):
        """Backward compatibility: the pre-existing direct path is untouched."""
        response = client_for(requester).post(
            api_url,
            {"items": [_item(budget_code_id=budget_code.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["items"][0]["budget_code_id"] == budget_code.id

    def test_description_does_not_influence_which_account_is_used(
        self, client_for, api_url, requester, category
    ):
        """
        No keyword/description-based classification exists - the same
        category_id resolves identically no matter what the free-text
        description says.
        """
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
        assert response.data["items"][0]["budget_code_id"] == category.account_chart_id
