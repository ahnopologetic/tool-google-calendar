import inspect
from datetime import datetime
from functools import partial
from typing import Any, Callable
from unittest.mock import MagicMock

from dateutil import parser


def parse_datetime(datetime_str: str) -> datetime:
    """
    Parses a datetime string into a datetime object. The string can be in various formats including
    yyyy-mm-dd, ISO format, and other common formats.

    Args:
        datetime_str: The datetime string to parse.

    Returns:
        A datetime object.
    """
    return parser.parse(datetime_str)


def function_to_schema(func: Callable[..., Any]) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    if isinstance(func, MagicMock): # TODO: Replace this with test double
        return {
            "type": "function",
            "function": {
                "name": "mock_function",
                "description": "This is a mock function used for testing.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    if isinstance(func, partial):
        original_func = func.func
        partial_args = func.keywords
    else:
        original_func = func
        partial_args = {}

    try:
        signature = inspect.signature(original_func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {original_func.__name__}: {str(e)}"
        )

    # Parse docstring to get parameter descriptions
    docstring = inspect.getdoc(original_func) or ""
    param_descriptions = {}
    for line in docstring.split("\n"):
        line = line.strip()
        if line.startswith(":param"):
            # Parse ":param param_name: description" format
            parts = line[6:].split(":", 1)
            if len(parts) == 2:
                param_name = parts[0].strip()
                description = parts[1].strip()
                param_descriptions[param_name] = description

    parameters = {}
    for param_name, param in signature.parameters.items():
        if param_name not in partial_args:
            try:
                param_type = type_map.get(param.annotation, "string")
            except KeyError as e:
                raise KeyError(
                    f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
                )
            param_info = {
                "type": param_type,
                "description": param_descriptions.get(param_name, ""),
            }
            parameters[param_name] = param_info

    required = [
        param_name
        for param_name, param in signature.parameters.items()
        if param.default == inspect._empty and param_name not in partial_args
    ]

    return {
        "type": "function",
        "function": {
            "name": original_func.__name__,
            "description": (original_func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
