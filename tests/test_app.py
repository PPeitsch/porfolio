# The fixtures 'app' and 'client' are now available from conftest.py


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"OK"
