import json
import yaml
from typing import Dict, Any
import os


class Config:
    """
    Configuration class to manage settings for the Google Calendar tool.
    """

    def __init__(self, config_path: str = "tools.yaml"):
        """
        Initializes the Config class by loading settings from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the configuration from the YAML file.

        Returns:
            A dictionary containing the configuration settings.
        """
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)
                return self._interpolate_env_vars(config)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")

    def _interpolate_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively interpolates environment variables in the configuration dictionary.

        Args:
            config: The configuration dictionary.

        Returns:
            The configuration dictionary with environment variables interpolated.
        """
        if isinstance(config, dict):
            return {k: self._interpolate_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._interpolate_env_vars(i) for i in config]
        elif isinstance(config, str):
            return os.path.expandvars(config)
        else:
            return config

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Retrieves the configuration for a specific tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            A dictionary containing the tool's configuration settings.
        """
        tools = self.config.get("tools", {})
        if tool_name not in tools:
            raise ValueError(f"Configuration for tool '{tool_name}' not found.")
        return tools[tool_name]

    def get_credential_path(self, tool_name: str) -> str | None:
        """
        Retrieves the credential path for a specific tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            The path to the credentials file for the tool.
        """
        tool_config = self.get_tool_config(tool_name)
        credential_path = tool_config.get("credential", {}).get("path")
        if not credential_path:
            return None

        return credential_path

    def get_credential_value(self, tool_name: str) -> Dict[str, Any] | None:
        """
        Retrieves the credentials value for a specific tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            The credentials value for the tool. (optional)
        """
        tool_config = self.get_tool_config(tool_name)
        credentials_value_str = tool_config.get("credential", {}).get("value")
        if not credentials_value_str:
            return None

        return json.loads(credentials_value_str)

    def get_default_calendar_id(self, tool_name: str) -> str:
        """
        Retrieves the default calendar ID for a specific tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            The default calendar ID for the tool.
        """
        tool_config = self.get_tool_config(tool_name)
        default_calendar_id = tool_config.get("default", {}).get("calendar_id")
        if not default_calendar_id:
            raise ValueError(
                f"Default calendar ID not specified for tool '{tool_name}'."
            )
        return default_calendar_id
