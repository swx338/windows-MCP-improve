from unittest.mock import patch, MagicMock

import pytest
import requests

from windows_mcp.auth.service import AuthClient, AuthError, MAX_RETRIES, RETRY_BACKOFF


class TestAuthError:
    def test_message(self):
        err = AuthError("something failed")
        assert str(err) == "something failed"
        assert err.message == "something failed"
        assert err.status_code is None

    def test_with_status_code(self):
        err = AuthError("unauthorized", status_code=401)
        assert err.status_code == 401


class TestAuthClientProperties:
    def test_proxy_url(self):
        client = AuthClient(api_key="key", sandbox_id="sb-1")
        assert client.proxy_url.endswith("/api/mcp")

    def test_proxy_headers_before_auth(self):
        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="Not authenticated"):
            _ = client.proxy_headers

    def test_proxy_headers_after_auth(self):
        client = AuthClient(api_key="key", sandbox_id="sb-1")
        client._session_token = "tok-123"
        headers = client.proxy_headers
        assert headers == {"Authorization": "Bearer tok-123"}

    def test_session_token_initially_none(self):
        client = AuthClient(api_key="key", sandbox_id="sb-1")
        assert client.session_token is None

    def test_repr_masks_key(self):
        client = AuthClient(api_key="sk-wmcp-abcdefghijklmnopqrst", sandbox_id="sb-1")
        r = repr(client)
        assert "sk-wmcp-abcd" in r
        assert "qrst" in r
        assert "abcdefghijklmnopqrst" not in r

    def test_repr_short_key(self):
        client = AuthClient(api_key="short", sandbox_id="sb-1")
        r = repr(client)
        assert "***" in r


class TestAuthenticate:
    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_success(self, mock_post, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_token": "tok-abc"}
        mock_post.return_value = mock_response

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        client.authenticate()

        assert client.session_token == "tok-abc"
        mock_post.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_connection_error_retries(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.ConnectionError()

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="Cannot reach dashboard"):
            client.authenticate()

        assert mock_post.call_count == MAX_RETRIES

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_timeout_retries(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.Timeout()

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="timed out"):
            client.authenticate()

        assert mock_post.call_count == MAX_RETRIES

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_non_json_response_retries(self, mock_post, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.json.side_effect = ValueError("not json")
        mock_post.return_value = mock_response

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="non-JSON response"):
            client.authenticate()

        assert mock_post.call_count == MAX_RETRIES

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_4xx_no_retry(self, mock_post, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid API key"}
        mock_post.return_value = mock_response

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="Invalid API key") as exc_info:
            client.authenticate()

        assert exc_info.value.status_code == 401
        mock_post.assert_called_once()

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_5xx_retries(self, mock_post, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}
        mock_post.return_value = mock_response

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="Internal error") as exc_info:
            client.authenticate()

        assert exc_info.value.status_code == 500
        assert mock_post.call_count == MAX_RETRIES

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_missing_session_token(self, mock_post, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError, match="no session_token"):
            client.authenticate()

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_retry_then_success(self, mock_post, mock_sleep):
        fail_response = MagicMock()
        fail_response.side_effect = requests.ConnectionError()

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"session_token": "tok-retry"}

        mock_post.side_effect = [requests.ConnectionError(), success_response]

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        client.authenticate()

        assert client.session_token == "tok-retry"
        assert mock_post.call_count == 2

    @patch("windows_mcp.auth.service.time.sleep")
    @patch("windows_mcp.auth.service.requests.post")
    def test_backoff_timing(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.Timeout()

        client = AuthClient(api_key="key", sandbox_id="sb-1")
        with pytest.raises(AuthError):
            client.authenticate()

        # Backoff: attempt 1 -> sleep 2s, attempt 2 -> sleep 4s, attempt 3 -> no sleep
        assert mock_sleep.call_count == MAX_RETRIES - 1
        mock_sleep.assert_any_call(RETRY_BACKOFF)
        mock_sleep.assert_any_call(RETRY_BACKOFF * 2)
