"""
Integration tests for the HR company calendar events API
(GET/POST /api/v2/hr/events/, GET/PUT/PATCH/DELETE /api/v2/hr/events/<id>/).
"""
import pytest
from rest_framework import status

pytestmark = pytest.mark.integration

LIST_URL = "/api/v2/hr/events/"


def detail_url(event_id):
    return f"/api/v2/hr/events/{event_id}/"


@pytest.mark.django_db
class TestHRCalendarEventsAPI:
    def test_list_events_empty(self, admin_client, enable_all_system_modules):
        response = admin_client.get(LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_create_event_success(self, admin_client, enable_all_system_modules):
        payload = {
            "title": "Public Holiday",
            "description": "Independence Day",
            "event_type": "Holiday",
            "start_date": "2026-04-18",
            "end_date": "2026-04-18",
            "is_all_day": True,
            "location": "",
        }
        response = admin_client.post(LIST_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Public Holiday"
        assert data["event_type"] == "Holiday"
        assert data["is_all_day"] is True

    def test_create_event_missing_required_fields(self, admin_client, enable_all_system_modules):
        response = admin_client.post(LIST_URL, {"title": "No dates"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_events_after_create(self, admin_client, enable_all_system_modules):
        admin_client.post(
            LIST_URL,
            {"title": "Team Meeting", "start_date": "2026-05-01", "end_date": "2026-05-01"},
            format="json",
        )
        response = admin_client.get(LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Team Meeting"

    def test_get_event_detail_and_not_found(self, admin_client, enable_all_system_modules):
        create_resp = admin_client.post(
            LIST_URL,
            {"title": "Training Day", "start_date": "2026-06-10", "end_date": "2026-06-11"},
            format="json",
        )
        event_id = create_resp.json()["id"]

        response = admin_client.get(detail_url(event_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Training Day"

        response = admin_client.get(detail_url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_event_put_and_patch(self, admin_client, enable_all_system_modules):
        create_resp = admin_client.post(
            LIST_URL,
            {"title": "Draft Event", "start_date": "2026-07-01", "end_date": "2026-07-01"},
            format="json",
        )
        event_id = create_resp.json()["id"]

        response = admin_client.patch(detail_url(event_id), {"title": "Confirmed Event"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Confirmed Event"

        response = admin_client.put(
            detail_url(event_id),
            {
                "title": "Confirmed Event",
                "start_date": "2026-07-02",
                "end_date": "2026-07-02",
                "location": "Boardroom",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["location"] == "Boardroom"

    def test_delete_event(self, admin_client, enable_all_system_modules):
        create_resp = admin_client.post(
            LIST_URL,
            {"title": "To Delete", "start_date": "2026-08-01", "end_date": "2026-08-01"},
            format="json",
        )
        event_id = create_resp.json()["id"]

        response = admin_client.delete(detail_url(event_id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = admin_client.get(detail_url(event_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication(self):
        from rest_framework.test import APIClient

        response = APIClient().get(LIST_URL)
        assert response.status_code in (401, 403)
