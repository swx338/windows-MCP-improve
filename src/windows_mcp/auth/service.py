import requests
import logging
import time

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each attempt


class AuthError(Exception):
    """Raised when authentication with the dashboard fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthClient:
    """
    Handles authentication between the MCP server (running on EC2)
    and the Windows-MCP Dashboard.

    Flow:
        1. POST /api/user/auth with api_key + sandbox_id
        2. Dashboard validates key, checks credits, resolves sandbox
        3. Returns session_token for subsequent /api/mcp calls
        4. ProxyClient uses Bearer <session_token> to connect
    """

    def __init__(self, api_key: str, sandbox_id: str):
        self.dashboard_url = "http://localhost:3000"
        self.api_key = api_key
        self.sandbox_id = sandbox_id
        self._session_token: str | None = None

    @property
    def session_token(self) -> str | None:
        return self._session_token

    @property
    def proxy_url(self) -> str:
        """The dashboard's MCP streamable-HTTP endpoint."""
        return f"{self.dashboard_url}/api/mcp"

    @property
    def proxy_headers(self) -> dict[str, str]:
        """Headers for ProxyClient with Bearer auth."""
        if not self._session_token:
            raise AuthError("Not authenticated. Call authenticate() first.")
        return {"Authorization": f"Bearer {self._session_token}"}

    def authenticate(self) -> None:
        """
        Authenticate with the dashboard and obtain a session token.
        Retries up to MAX_RETRIES times on transient failures.

        Raises:
            AuthError: If authentication fails after all retries.
        """
        url = f"{self.dashboard_url}/api/user/auth"
        payload = {
            "api_key": self.api_key,
            "sandbox_id": self.sandbox_id,
        }

        last_error: AuthError | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            logger.info("Authenticating with dashboard at %s (attempt %d/%d)", url, attempt, MAX_RETRIES)

            try:
                response = requests.post(url, json=payload, timeout=30)
            except requests.ConnectionError:
                last_error = AuthError(
                    f"Cannot reach dashboard at {self.dashboard_url}. "
                    "Check DASHBOARD_URL and network connectivity."
                )
                self._backoff(attempt)
                continue
            except requests.Timeout:
                last_error = AuthError("Dashboard authentication request timed out.")
                self._backoff(attempt)
                continue
            except requests.RequestException as e:
                last_error = AuthError(f"Request failed: {e}")
                self._backoff(attempt)
                continue

            try:
                data = response.json()
            except (ValueError, requests.JSONDecodeError):
                last_error = AuthError(
                    f"Dashboard returned non-JSON response (HTTP {response.status_code})."
                )
                self._backoff(attempt)
                continue

            if response.status_code != 200:
                detail = data.get("detail", "Unknown error")
                logger.error("Authentication failed [%d]: %s", response.status_code, detail)
                # Don't retry on client errors (4xx) — these won't resolve themselves
                if 400 <= response.status_code < 500:
                    raise AuthError(detail, status_code=response.status_code)
                last_error = AuthError(detail, status_code=response.status_code)
                self._backoff(attempt)
                continue

            session_token = data.get("session_token")
            if not session_token:
                raise AuthError(
                    "Dashboard returned success but no session_token. "
                    "Ensure the dashboard is up to date."
                )

            self._session_token = session_token
            logger.info("Authenticated successfully. Session token obtained.")
            return

        raise last_error

    @staticmethod
    def _backoff(attempt: int) -> None:
        """Sleep with exponential backoff between retry attempts."""
        if attempt < MAX_RETRIES:
            delay = RETRY_BACKOFF * (2 ** (attempt - 1))
            logger.warning("Retrying in %ds...", delay)
            time.sleep(delay)

    def __repr__(self) -> str:
        masked_key = f"{self.api_key[:12]}...{self.api_key[-4:]}" if len(self.api_key) > 16 else "***"
        return (
            f"AuthClient(dashboard={self.dashboard_url!r}, "
            f"sandbox={self.sandbox_id!r}, key={masked_key})"
        )
