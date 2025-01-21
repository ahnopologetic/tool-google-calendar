from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .config import Config

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendar:
    def __init__(self, config_path: str = "tools.yaml", tool_name: str = "google-calendar"):
        """
        Initializes the GoogleCalendar tool with user credentials and builds the service object.

        Args:
            config_path: Path to the YAML configuration file.
            tool_name: The name of the tool in the configuration file.
        """
        config = Config(config_path)
        self.tool_config = config.get_tool_config(tool_name)
        self.credentials_path = config.get_credential_path(tool_name)
        self.default_calendar_id = config.get_default_calendar_id(tool_name)
        self.credentials = self._load_credentials(self.credentials_path)
        self.service = build("calendar", "v3", credentials=self.credentials)

    def _load_credentials(self, credentials_path: str) -> Credentials:
        """
        Loads user credentials from a file.

        Args:
            credentials_path: Path to the credentials file.

        Returns:
            Google OAuth2 credentials.
        """
        # Replace this with your actual credential loading logic
        # This is a placeholder for demonstration purposes
        creds = Credentials.from_authorized_user_file(credentials_path, SCOPES)
        return creds

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str = None,
        location: str = None,
    ) -> str:
        """
        Creates a new event in the user's primary calendar.

        Args:
            summary: The title of the event.
            start_time: The start time of the event (datetime object).
            end_time: The end time of the event (datetime object).
            description: The description of the event (optional).
            location: The location of the event (optional).

        Returns:
            The ID of the created event.
        """
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Los_Angeles",  # Replace with your timezone
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Los_Angeles",  # Replace with your timezone
            },
        }

        created_event = (
            self.service.events().insert(calendarId=self.default_calendar_id, body=event).execute()
        )
        return created_event.get("id")

    def get_events(self, time_min: datetime, time_max: datetime) -> list:
        """
        Retrieves events within a specified time range.

        Args:
            time_min: The minimum time (inclusive) for events to be retrieved.
            time_max: The maximum time (exclusive) for events to be retrieved.

        Returns:
            A list of events.
        """
        events_result = (
            self.service.events()
            .list(
                calendarId=self.default_calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events

    def get_event(self, event_id: str) -> dict:
        """
        Retrieves a specific event by its ID.

        Args:
            event_id: The ID of the event to retrieve.

        Returns:
            The event details.
        """
        event = (
            self.service.events().get(calendarId=self.default_calendar_id, eventId=event_id).execute()
        )
        return event

    def update_event(
        self,
        event_id: str,
        summary: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        description: str = None,
        location: str = None,
    ) -> dict:
        """
        Updates an existing event.

        Args:
            event_id: The ID of the event to update.
            summary: The new title of the event (optional).
            start_time: The new start time of the event (optional).
            end_time: The new end time of the event (optional).
            description: The new description of the event (optional).
            location: The new location of the event (optional).

        Returns:
            The updated event details.
        """
        event = (
            self.service.events().get(calendarId=self.default_calendar_id, eventId=event_id).execute()
        )

        if summary:
            event["summary"] = summary
        if start_time:
            event["start"]["dateTime"] = start_time.isoformat()
        if end_time:
            event["end"]["dateTime"] = end_time.isoformat()
        if description:
            event["description"] = description
        if location:
            event["location"] = location

        updated_event = (
            self.service.events()
            .update(calendarId=self.default_calendar_id, eventId=event_id, body=event)
            .execute()
        )
        return updated_event

    def delete_event(self, event_id: str) -> None:
        """
        Deletes an event by its ID.

        Args:
            event_id: The ID of the event to delete.
        """
        self.service.events().delete(calendarId=self.default_calendar_id, eventId=event_id).execute()

    @property
    def functions(self):
        """
        Returns the list of available functions in a format suitable for OpenAI's API.
        """
        return [
            {
                "name": "google_calendar_create_event",
                "description": "Creates a new event in the user's Google Calendar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "The title of the event.",
                        },
                        "start_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The start time of the event (ISO 8601 format).",
                        },
                        "end_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The end time of the event (ISO 8601 format).",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the event.",
                        },
                        "location": {
                            "type": "string",
                            "description": "The location of the event.",
                        },
                    },
                    "required": ["summary", "start_time", "end_time"],
                },
            },
            {
                "name": "google_calendar_get_events",
                "description": "Retrieves events from the user's Google Calendar within a specified time range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_min": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The minimum time (inclusive) for events to be retrieved (ISO 8601 format).",
                        },
                        "time_max": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The maximum time (exclusive) for events to be retrieved (ISO 8601 format).",
                        },
                    },
                    "required": ["time_min", "time_max"],
                },
            },
            {
                "name": "google_calendar_get_event",
                "description": "Retrieves a specific event from the user's Google Calendar by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to retrieve.",
                        },
                    },
                    "required": ["event_id"],
                },
            },
            {
                "name": "google_calendar_update_event",
                "description": "Updates an existing event in the user's Google Calendar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to update.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "The new title of the event.",
                        },
                        "start_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The new start time of the event (ISO 8601 format).",
                        },
                        "end_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "The new end time of the event (ISO 8601 format).",
                        },
                        "description": {
                            "type": "string",
                            "description": "The new description of the event.",
                        },
                        "location": {
                            "type": "string",
                            "description": "The new location of the event.",
                        },
                    },
                    "required": ["event_id"],
                },
            },
            {
                "name": "google_calendar_delete_event",
                "description": "Deletes an event from the user's Google Calendar by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to delete.",
                        },
                    },
                    "required": ["event_id"],
                },
            },
        ]
