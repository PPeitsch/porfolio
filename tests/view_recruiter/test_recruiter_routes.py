import json
from unittest.mock import MagicMock, patch

from tests.helpers import generate_test_token


@patch("app.view_recruiter.routes.get_llm_service")
def test_chat_simple_text_response(mock_get_llm_service, client, app):
    """
    Test a simple chat interaction where the LLM returns a direct text response.
    """
    # Arrange
    mock_service = MagicMock()
    mock_service.get_chat_response.return_value = "Hello from the mock LLM!"
    mock_get_llm_service.return_value = mock_service

    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "Hi there!", "history": []}

    # Act
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    response_data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert response_data["reply"] == "Hello from the mock LLM!"
    mock_service.get_chat_response.assert_called_once()


@patch("app.view_recruiter.routes.get_llm_service")
@patch("app.view_recruiter.routes.TOOL_MAP")
def test_chat_with_tool_use(mock_tool_map, mock_get_llm_service, client, app):
    """
    Test a chat interaction that involves a tool call.
    """
    # --- Arrange ---
    # 1. Mock the LLM service to first request a tool, then give a final answer.
    mock_service = MagicMock()
    mock_service.get_chat_response.side_effect = [
        # First call: LLM asks to use a tool
        [
            {
                "id": "tool123",
                "name": "get_project_list",
                "input": {},
            }
        ],
        # Second call: LLM gives final response based on tool output
        "Here are the projects: Project A, Project B.",
    ]
    mock_get_llm_service.return_value = mock_service

    # 2. Mock the tool function itself
    mock_project_list_func = MagicMock(return_value=["Project A", "Project B"])
    # Configure the mocked TOOL_MAP to return our mocked function
    mock_tool_map.__getitem__.side_effect = lambda key: {
        "get_project_list": mock_project_list_func
    }.get(key)
    mock_tool_map.__contains__.return_value = True

    # 3. Prepare request payload
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"message": "What projects do you have?", "history": []}

    # --- Act ---
    response = client.post(
        "/recruiter/api/chat", headers=headers, data=json.dumps(payload)
    )
    response_data = response.get_json()

    # --- Assert ---
    assert response.status_code == 200
    assert response_data["reply"] == "Here are the projects: Project A, Project B."

    # Assert that the LLM service was called twice (once for tool, once for answer)
    assert mock_service.get_chat_response.call_count == 2
    # Assert that our project list tool function was called
    mock_project_list_func.assert_called_once()


def test_chat_unauthorized(client):
    """Test that the chat endpoint requires authorization."""
    response = client.post(
        "/recruiter/api/chat",
        data=json.dumps({"message": "test"}),
        content_type="application/json",
    )
    assert response.status_code == 401
