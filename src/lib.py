from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from src.utils import function_to_schema, parse_datetime
from .config import Config

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendar:
    def __init__(
        self, config_path: str = "tools.yaml", tool_name: str = "google-calendar"
    ):
        """
        Initializes the GoogleCalendar tool with user credentials and builds the service object.

        Args:
            config_path: Path to the YAML configuration file.
            tool_name: The name of the tool in the configuration file.
        """
        config = Config(config_path)
        self.tool_config = config.get_tool_config(tool_name)
        self.credentials_value = config.get_credential_value(tool_name)
        self.credentials_path = config.get_credential_path(tool_name)
        self.default_calendar_id = config.get_default_calendar_id(tool_name)
        self.credentials = self._load_credentials(
            self.credentials_path, credential_value=self.credentials_value
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    def _load_credentials(
        self, credentials_path: str | None, credential_value: dict | None = None
    ) -> Credentials:
        """
        Loads user credentials from a file.

        Args:
            credentials_path: Path to the credentials file.

        Returns:
            Google OAuth2 credentials.
        """
        if not credentials_path and not credential_value:
            raise ValueError("No credentials provided.")

        if credential_value:
            creds = Credentials.from_authorized_user_info(credential_value, SCOPES)
        else:
            creds = Credentials.from_authorized_user_file(credentials_path, SCOPES)
        return creds

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = None,
        location: str = None,
    ) -> str:
        """
        Creates a new event in the user's primary calendar.

        Args:
            summary: The title of the event.
            start_time: The start time of the event.
            end_time: The end time of the event.
            description: The description of the event (optional).
            location: The location of the event (optional).

        Returns:
            The ID of the created event.
        """
        start_time_dt = parse_datetime(start_time)
        end_time_dt = parse_datetime(end_time)

        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time_dt.isoformat(),
                "timeZone": "America/Los_Angeles",  # Replace with your timezone
            },
            "end": {
                "dateTime": end_time_dt.isoformat(),
                "timeZone": "America/Los_Angeles",  # Replace with your timezone
            },
        }

        created_event = (
            self.service.events()
            .insert(calendarId=self.default_calendar_id, body=event)
            .execute()
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
            self.service.events()
            .get(calendarId=self.default_calendar_id, eventId=event_id)
            .execute()
        )
        return event

    def update_event(
        self,
        event_id: str,
        summary: str = None,
        start_time: str = None,
        end_time: str = None,
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
            self.service.events()
            .get(calendarId=self.default_calendar_id, eventId=event_id)
            .execute()
        )

        if summary:
            event["summary"] = summary
        if start_time:
            start_time_dt = parse_datetime(start_time)
            event["start"]["dateTime"] = start_time_dt.isoformat()
        if end_time:
            end_time_dt = parse_datetime(end_time)
            event["end"]["dateTime"] = end_time_dt.isoformat()
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
        self.service.events().delete(
            calendarId=self.default_calendar_id, eventId=event_id
        ).execute()

    @property
    def functions(self):
        """
        Returns the list of available functions in a format suitable for OpenAI's API.
        """
        return [
            function_to_schema(getattr(self, method))
            for method in dir(GoogleCalendar)
            if callable(getattr(GoogleCalendar, method)) and not method.startswith("_")
        ]
