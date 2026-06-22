"""Bridge Admin Login UI requests to the authentication repository layer."""

from pathlib import Path

from database.connection import DB_NAME
from database.repositories.admin_repository import authenticate_admin


class AuthController:
    """Coordinate authentication between the PySide6 UI and database access."""

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Store the database target used for Admin Panel authentication."""
        self.db_path = db_path

    def login(self, username: str, password: str) -> dict | None:
        """Return safe admin data when the supplied credentials are valid."""
        normalized_username = username.strip()
        if not normalized_username or not password:
            return None

        return authenticate_admin(normalized_username, password, self.db_path)
