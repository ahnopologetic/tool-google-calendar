from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import json
from src import GoogleCalendar  # Assuming this is your tool


# Mock the OpenAI API response
@pytest.fixture
def mock_openai_chatcompletion():
    with patch("openai.ChatCompletion.create") as mock_create:
        yield mock_create


# Test successful function call
def test_successful_function_call(
    mock_openai_chatcompletion,
    google_calendar_credential_path: str,
):
    # Mock the API response to simulate a function call
    mock_openai_chatcompletion.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": "google_calendar_create_event",
                        "arguments": json.dumps(
                            {
                                "summary": "Test Event",
                                "start_time": "2023-12-28T09:00:00",
                                "end_time": "2023-12-28T10:00:00",
                            }
                        ),
                    },
                }
            }
        ]
    }

    # Create an instance of your Google Calendar tool
    calendar_tool = GoogleCalendar(config_path="tests/data/tools.yaml")

    # Mock the create_event function
    with patch.object(
        calendar_tool, "create_event", return_value="Event Created"
    ) as mock_create_event:
        # Define the available functions
        available_functions = {
            "google_calendar_create_event": calendar_tool.create_event,
        }

        # Simulate the conversation messages
        messages = [
            {
                "role": "user",
                "content": "Create a calendar event for tomorrow at 9 am called Test Event",
            }
        ]

        # Call the OpenAI API (mocked)
        response = mock_openai_chatcompletion(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            functions=calendar_tool.functions,
        )

        # Get the response message
        response_message = response["choices"][0]["message"]

        # Check if a function call is required
        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])

            # Call the function
            function_to_call(**function_args)

            # Assert that the function was called with the correct arguments
            mock_create_event.assert_called_once_with(
                summary="Test Event",
                start_time="2023-12-28T09:00:00",
                end_time="2023-12-28T10:00:00",
            )


# Test error handling
def test_function_call_error_handling(
    mock_openai_chatcompletion,
    google_calendar_credential_path: str,
):
    # Mock the API response to simulate a function call with invalid arguments
    mock_openai_chatcompletion.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": "google_calendar_create_event",
                        "arguments": json.dumps({"invalid_arg": "value"}),
                    },
                }
            }
        ]
    }

    # Create an instance of your Google Calendar tool
    calendar_tool = GoogleCalendar(config_path="tests/data/tools.yaml")

    # Define the available functions
    available_functions = {
        "google_calendar_create_event": calendar_tool.create_event,
    }

    # Simulate the conversation messages
    messages = [
        {"role": "user", "content": "Create a calendar event with invalid arguments"}
    ]

    # Call the OpenAI API (mocked)
    response = mock_openai_chatcompletion(
        model="gpt-3.5-turbo-0613", messages=messages, functions=calendar_tool.functions
    )

    # Get the response message
    response_message = response["choices"][0]["message"]

    # Check if a function call is required
    if response_message.get("function_call"):
        function_name = response_message["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])

        # Call the function and expect an error
        with pytest.raises(Exception):
            function_response = function_to_call(**function_args)


def test_function_definition_is_correct():
    # Create an instance of your Google Calendar tool
    calendar_tool = GoogleCalendar(config_path="tests/data/tools.yaml")

    for function in calendar_tool.functions:
        assert function["type"] == "function"
        assert "function" in function
        assert "name" in function["function"]
        assert "description" in function["function"]
        assert "parameters" in function["function"]
        assert "type" in function["function"]["parameters"]
        assert function["function"]["parameters"]["type"] == "object"
        assert "properties" in function["function"]["parameters"]
        assert "required" in function["function"]["parameters"]
        assert isinstance(function["function"]["parameters"]["properties"], dict)
        assert isinstance(function["function"]["parameters"]["required"], list)


@pytest.mark.parametrize(
    "config_path",
    [
        "tests/data/tools.yaml",
        "tests/data/tools-inline-json.yaml",
        "tests/data/tools-multiple-tools.yaml",
    ],
)
def test_inline_credential_init_should_pass(config_path: str):
    calendar_tool = GoogleCalendar(config_path=config_path)

    assert calendar_tool.default_calendar_id == "primary"
    assert calendar_tool.credentials is not None
