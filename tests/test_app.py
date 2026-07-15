import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Keep test cases isolated by restoring in-memory activity data."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_catalog():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]


def test_signup_adds_new_participant():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "new_student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post("/activities/Unknown Club/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    # Arrange
    client = TestClient(app)
    activity_name = "Programming Class"
    existing_email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_delete_participant_removes_existing_student():
    # Arrange
    client = TestClient(app)
    activity_name = "Drama Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity_name}/delete-participant", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_delete_participant_rejects_missing_student():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete(
        "/activities/Drama Club/delete-participant",
        params={"email": "not_enrolled@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_delete_participant_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete(
        "/activities/Unknown Club/delete-participant",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
