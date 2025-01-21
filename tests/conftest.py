import pytest
import json
import os
import tempfile


@pytest.fixture(scope="session")
def google_calendar_credential_path():
    """
    Fixture to create a temporary credentials.json file for testing.
    """
    credentials_data = {
        "client_id": "dummy_client_id",
        "project_id": "dummy_project_id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "dummy_client_secret",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "refresh_token": "dummy_refresh_token",
    }

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as tmp_file:
        json.dump(credentials_data, tmp_file)
        tmp_file_path = tmp_file.name

    yield tmp_file_path

    # Clean up the temporary file after tests are done
    os.unlink(tmp_file_path)


@pytest.fixture(scope="session", autouse=True)
def setup_environment(google_calendar_credential_path):
    """
    Fixture to set the GOOGLE_CALENDAR_CREDENTIAL_JSON environment variable.
    """
    os.environ["GOOGLE_CALENDAR_CREDENTIAL_JSON"] = google_calendar_credential_path
    yield
    del os.environ["GOOGLE_CALENDAR_CREDENTIAL_JSON"]
