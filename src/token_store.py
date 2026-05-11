"""Local Gmail token storage for the stdio Gmail agent."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailTokenStore:
    """Encrypted local token store for Gmail users."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".gmail-mcp"
        self.config_dir.mkdir(exist_ok=True)

        self.tokens_dir = self.config_dir / "tokens"
        self.tokens_dir.mkdir(exist_ok=True)

        self.credentials_file = self.config_dir / "credentials.json"
        self.current_user_file = self.config_dir / "current_user.json"
        self.key_file = self.config_dir / ".key"

        self._ensure_encryption_key()

    def _ensure_encryption_key(self) -> None:
        if not self.key_file.exists():
            self.key_file.write_bytes(Fernet.generate_key())
            self.key_file.chmod(0o600)

    def _get_cipher(self) -> Fernet:
        return Fernet(self.key_file.read_bytes())

    def _encrypt_data(self, data: dict[str, Any]) -> bytes:
        return self._get_cipher().encrypt(json.dumps(data).encode())

    def _decrypt_data(self, encrypted_data: bytes) -> dict[str, Any]:
        return json.loads(self._get_cipher().decrypt(encrypted_data).decode())

    def _token_id_for_email(self, email: str) -> str:
        normalized_email = email.strip().lower().encode()
        return hashlib.sha256(normalized_email).hexdigest()

    def _token_file_for_id(self, token_id: str) -> Path:
        return self.tokens_dir / f"{token_id}.json"

    def _legacy_token_files(self) -> list[Path]:
        return [
            path
            for path in self.tokens_dir.glob("*.json")
            if "@" in path.stem or "." in path.stem
        ]

    def _read_token_data(self, token_file: Path) -> dict[str, Any]:
        return self._decrypt_data(token_file.read_bytes())

    def _write_token_data(self, token_id: str, token_data: dict[str, Any]) -> None:
        token_file = self._token_file_for_id(token_id)
        token_file.write_bytes(self._encrypt_data(token_data))
        token_file.chmod(0o600)

    def migrate_legacy_storage(self) -> None:
        """Migrate raw-email token filenames and current-user pointers."""
        migrated: dict[str, str] = {}
        for legacy_file in self._legacy_token_files():
            token_data = self._read_token_data(legacy_file)
            email = token_data.get("email") or legacy_file.stem
            token_id = self._token_id_for_email(email)
            self._write_token_data(token_id, {**token_data, "email": email})
            legacy_file.unlink()
            migrated[email] = token_id

        current_token_id = self._read_current_token_id()
        if current_token_id and "@" in current_token_id:
            token_id = migrated.get(current_token_id) or self._token_id_for_email(
                current_token_id
            )
            if self._token_file_for_id(token_id).exists():
                self._write_current_token_id(token_id)

    def set_credentials_file(self, credentials_path: str) -> None:
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

        with open(credentials_path) as src:
            credentials_data = json.load(src)

        with open(self.credentials_file, "w") as dst:
            json.dump(credentials_data, dst, indent=2)

        self.credentials_file.chmod(0o600)

    def authenticate_user(self) -> str:
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                "OAuth2 credentials not found. Please set credentials file first."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_file), SCOPES
        )

        try:
            creds = flow.run_local_server(port=0, open_browser=False)
        except Exception:
            creds = flow.run_console()

        from googleapiclient.discovery import build

        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        user_email = profile["emailAddress"]

        self.save_credentials(user_email, creds)
        self.set_current_user(user_email)
        return user_email

    def save_credentials(self, email: str, credentials: Credentials) -> None:
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "email": email,
        }
        self._write_token_data(self._token_id_for_email(email), token_data)

    def get_credentials(self, email: Optional[str] = None) -> Optional[Credentials]:
        self.migrate_legacy_storage()
        token_id = (
            self._token_id_for_email(email) if email else self._read_current_token_id()
        )
        if not token_id:
            return None

        token_file = self._token_file_for_id(token_id)
        if not token_file.exists():
            return None

        token_data = self._read_token_data(token_file)
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data["scopes"],
        )

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_data.update(
                    {"token": creds.token, "refresh_token": creds.refresh_token}
                )
                self._write_token_data(token_id, token_data)
            else:
                return None

        return creds

    def _read_current_token_id(self) -> Optional[str]:
        if not self.current_user_file.exists():
            return None

        try:
            with open(self.current_user_file) as f:
                data = json.load(f)
        except Exception:
            return None

        return data.get("token_id") or data.get("email")

    def _write_current_token_id(self, token_id: str) -> None:
        with open(self.current_user_file, "w") as f:
            json.dump({"token_id": token_id}, f, indent=2)
        self.current_user_file.chmod(0o600)

    def get_current_user(self) -> Optional[str]:
        self.migrate_legacy_storage()
        token_id = self._read_current_token_id()
        if not token_id:
            return None

        token_file = self._token_file_for_id(token_id)
        if not token_file.exists():
            return None

        try:
            return self._read_token_data(token_file).get("email")
        except Exception:
            return None

    def set_current_user(self, email: str) -> None:
        token_id = self._token_id_for_email(email)
        if not self._token_file_for_id(token_id).exists():
            raise ValueError(f"User not found or not authenticated: {email}")
        self._write_current_token_id(token_id)

    def list_users(self) -> list[str]:
        self.migrate_legacy_storage()
        users = []
        for token_file in self.tokens_dir.glob("*.json"):
            try:
                email = self._read_token_data(token_file).get("email")
            except Exception:
                email = None
            if email:
                users.append(email)
        return sorted(users)

    def remove_user(self, email: str) -> bool:
        self.migrate_legacy_storage()
        token_id = self._token_id_for_email(email)
        token_file = self._token_file_for_id(token_id)
        if not token_file.exists():
            return False

        token_file.unlink()
        if (
            self._read_current_token_id() == token_id
            and self.current_user_file.exists()
        ):
            self.current_user_file.unlink()
        return True

    def logout_current_user(self) -> bool:
        current_user = self.get_current_user()
        if not current_user:
            return False
        return self.remove_user(current_user)


AuthManager = GmailTokenStore
