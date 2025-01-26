import json
import pytest
import os
from src import GoogleCalendar
import openai


@pytest.mark.local_only
def test_integration_openai_function_call():
    assert "OPENAI_API_KEY" in os.environ, (
        "OPENAI_API_KEY environment variable is not set"
    )

    # Create an instance of your Google Calendar tool
    calendar_tool = GoogleCalendar(config_path="tests/data/tools.yaml")

    # Simulate the conversation messages
    messages = [
        {
            "role": "system",
            "content": "You are a calendar tool. Run current_datetime_utc to get the current date and time in UTC before any operation.",
        },
        {
            "role": "user",
            "content": "Create a calendar event for tomorrow at 9 am called Integration Test Event",
        },
    ]

    available_functions = {
        func: getattr(calendar_tool, func)
        for func in dir(GoogleCalendar)
        if callable(getattr(GoogleCalendar, func)) and not func.startswith("__")
    }

    client = openai.Client()
    max_cycles = 5

    for _ in range(max_cycles):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=calendar_tool.functions,
            tool_choice="auto",
        )

        # Get the response message
        response_message = response.choices[0].message

        # Check if a function call is required
        if response_message.tool_calls:
            function_call = response_message.tool_calls[0]
            function_name = function_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(function_call.function.arguments)

            # Call the function
            result = function_to_call(**function_args)

            # Append the function call result to the messages
            messages.append(
                response_message
            )
            messages.append(
                {"role": "tool", "content": result, "tool_call_id": function_call.id}
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Function {function_name} called with result: {result}",
                }
            )
        else:
            break


# should call get schedule from google calendar and update the time
# should call get schedule from google calendar and raise error when no event is found
# should call get schedule from google calendar and list them when multiple events are found
