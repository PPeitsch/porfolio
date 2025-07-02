import json
from unittest.mock import MagicMock, patch

from tests.helpers import generate_test_token


@patch("app.view_recruiter.routes.get_llm_service")
def test_chat_simple_text_response(mock_get_llm_service, client, app):
    """
    Test a simple chat interaction where the LLM returns a direct text response.
    """
    mock_service = MagicMock()
    mock_service.get_chat_response.return_value = "Hello from the mock LLM!"
    mock_get_llm_service.return_value = mock_service

    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "Hi there!", "history": []}

    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["reply"] == "Hello from the mock LLM!"
    mock_service.get_chat_response.assert_called_once()


@patch("app.view_recruiter.routes.get_llm_service")
@patch("app.view_recruiter.routes.TOOL_MAP")
def test_chat_with_tool_use(mock_tool_map, mock_get_llm_service, client, app):
    """
    Test a chat interaction that involves a tool call.
    """
    mock_service = MagicMock()
    mock_service.get_chat_response.side_effect = [
        [{"id": "tool123", "name": "get_project_list", "input": {}}],
        "Here are the projects: Project A, Project B.",
    ]
    mock_get_llm_service.return_value = mock_service

    mock_project_list_func = MagicMock(return_value=["Project A", "Project B"])
    mock_tool_map.__getitem__.side_effect = lambda key: {
        "get_project_list": mock_project_list_func
    }.get(key)
    mock_tool_map.__contains__.return_value = True

    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "What projects do you have?", "history": []}

    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["reply"] == "Here are the projects: Project A, Project B."
    assert mock_service.get_chat_response.call_count == 2
    mock_project_list_func.assert_called_once()


def test_chat_unauthorized(client):
    """Test that the chat endpoint requires authorization."""
    response = client.post(
        "/recruiter/api/chat",
        data=json.dumps({"message": "test"}),
        content_type="application/json",
    )
    assert response.status_code == 401


@patch("app.view_recruiter.routes.get_llm_service")
def test_chat_bad_request_no_message(mock_get_llm, client, app):
    """Test chat API with a payload missing the 'message' key."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"history": []}
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    assert response.status_code == 400
    assert "message' key is required" in response.get_json()["error"]


@patch("app.view_recruiter.routes.get_llm_service")
def test_chat_bad_request_empty_message(mock_get_llm, client, app):
    """Test chat API with an empty message string."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "   ", "history": []}
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    assert response.status_code == 400
    assert "must be a non-empty string" in response.get_json()["error"]


@patch("app.view_recruiter.routes.get_llm_service")
def test_chat_llm_service_not_configured(mock_get_llm, client, app):
    """Test chat API when the LLM service fails to initialize."""
    mock_get_llm.return_value = None
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "test", "history": []}
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    assert response.status_code == 503
    assert "not configured correctly" in response.get_json()["reply"]


@patch("app.view_recruiter.routes.get_llm_service")
@patch("app.view_recruiter.routes.TOOL_MAP", {})
def test_chat_tool_not_found(mock_get_llm_service, client, app):
    """Test chat handler when the LLM requests a tool that doesn't exist."""
    mock_service = MagicMock()
    mock_service.get_chat_response.side_effect = [
        [{"id": "t1", "name": "unknown_tool", "input": {}}],
        "Final fallback response",
    ]
    mock_get_llm_service.return_value = mock_service

    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps({"message": "test"})
    )
    assert response.status_code == 200
    assert response.get_json()["reply"] == "Final fallback response"
    # Check that the error was logged internally
    assert mock_service.get_chat_response.call_count == 2
