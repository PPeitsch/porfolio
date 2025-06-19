# The fixtures 'app' and 'client' are now available from conftest.py
import pytest


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"OK"


def test_selector_route(client):
    """Test that the main selector page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Select Your Experience" in response.data


@pytest.mark.parametrize(
    "view_name",
    ["cli", "recruiter", "visual"],
)
def test_get_view_partial_routes_success(client, view_name):
    """Test that valid view partials load successfully."""
    response = client.get(f"/view/{view_name}")
    assert response.status_code == 200
    # Check for a unique element in each view to confirm correct template rendering
    if view_name == "cli":
        assert b'id="cli-window"' in response.data
    elif view_name == "recruiter":
        assert b'id="chat-window"' in response.data
    elif view_name == "visual":
        assert b'id="visual-container"' in response.data


def test_get_view_partial_route_not_found(client):
    """Test that an invalid view partial returns a 404."""
    response = client.get("/view/nonexistentview")
    assert response.status_code == 404
    assert b'Error: View "nonexistentview" not found.' in response.data
