import json
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials

from src.token_store import GmailTokenStore, SCOPES


def make_credentials(token: str = "access-token") -> Credentials:
    credentials = Credentials(
        token=token,
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=SCOPES,
    )
    credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    return credentials


def test_saves_token_without_leaking_email_in_filename(tmp_path):
    store = GmailTokenStore(tmp_path)

    store.save_credentials("user@example.com", make_credentials())

    token_files = list((tmp_path / "tokens").glob("*.json"))
    assert len(token_files) == 1
    assert "user@example.com" not in token_files[0].name
    assert "@" not in token_files[0].name


def test_lists_users_from_encrypted_payloads(tmp_path):
    store = GmailTokenStore(tmp_path)

    store.save_credentials("second@example.com", make_credentials("second"))
    store.save_credentials("first@example.com", make_credentials("first"))

    assert store.list_users() == ["first@example.com", "second@example.com"]


def test_sets_and_resolves_current_user_with_private_pointer(tmp_path):
    store = GmailTokenStore(tmp_path)
    store.save_credentials("user@example.com", make_credentials())

    store.set_current_user("user@example.com")

    current_user_data = json.loads((tmp_path / "current_user.json").read_text())
    assert "email" not in current_user_data
    assert current_user_data["token_id"]
    assert store.get_current_user() == "user@example.com"


def test_migrates_legacy_raw_email_token_filename(tmp_path):
    store = GmailTokenStore(tmp_path)
    legacy_file = tmp_path / "tokens" / "user@example.com.json"
    legacy_file.write_bytes(
        store._encrypt_data(
            {
                "token": "access-token",
                "refresh_token": "refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "client-id",
                "client_secret": "client-secret",
                "scopes": SCOPES,
                "email": "user@example.com",
            }
        )
    )

    assert store.list_users() == ["user@example.com"]

    token_files = list((tmp_path / "tokens").glob("*.json"))
    assert len(token_files) == 1
    assert token_files[0].name != "user@example.com.json"
    assert not legacy_file.exists()


def test_migrates_legacy_current_user_email_pointer(tmp_path):
    store = GmailTokenStore(tmp_path)
    store.save_credentials("user@example.com", make_credentials())
    (tmp_path / "current_user.json").write_text(
        json.dumps({"email": "user@example.com"})
    )

    assert store.get_current_user() == "user@example.com"

    current_user_data = json.loads((tmp_path / "current_user.json").read_text())
    assert "email" not in current_user_data
    assert current_user_data["token_id"]
