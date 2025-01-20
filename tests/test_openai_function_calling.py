from unittest.mock import patch
import pytest
import json
from src import GoogleCalendar  # Assuming this is your tool



# Mock the OpenAI API response
@pytest.fixture
def mock_openai_chatcompletion():
    with patch("openai.ChatCompletion.create") as mock_create:
        yield mock_create


# Test successful function call
def test_successful_function_call(mock_openai_chatcompletion):
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
    calendar_tool = GoogleCalendar()

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
        model="gpt-3.5-turbo-0613", messages=messages, functions=calendar_tool.functions
    )

    # Get the response message
    response_message = response["choices"][0]["message"]

    # Check if a function call is required
    if response_message.get("function_call"):
        function_name = response_message["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])

        # Call the function
        function_response = function_to_call(**function_args)

        # Assert that the function was called with the correct arguments
        assert function_response is not None  # Assuming your function returns something
        # Add more specific assertions based on your function's behavior


# Test error handling
def test_function_call_error_handling(mock_openai_chatcompletion):
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
    calendar_tool = GoogleCalendar()

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


# Add more test cases as needed, e.g., for different functions, edge cases, etc.
