from unittest.mock import patch, MagicMock
from types import SimpleNamespace

import pytest

from windows_mcp.desktop.service import Desktop


@pytest.fixture
def desktop():
    with patch.object(Desktop, '__init__', lambda self: None):
        return Desktop()


class TestGetSystemInfo:
    def test_returns_all_sections(self, desktop):
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value = SimpleNamespace(
            percent=60.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = SimpleNamespace(
            percent=45.0, used=200 * 1024**3, total=500 * 1024**3
        )
        mock_psutil.boot_time.return_value = 1700000000.0
        mock_psutil.net_io_counters.return_value = SimpleNamespace(
            bytes_sent=100 * 1024**2, bytes_recv=500 * 1024**2
        )

        mock_platform = MagicMock()
        mock_platform.system.return_value = "Windows"
        mock_platform.release.return_value = "10"
        mock_platform.version.return_value = "10.0.19045"
        mock_platform.machine.return_value = "AMD64"

        import builtins
        _real_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "psutil":
                return mock_psutil
            if name == "platform":
                return mock_platform
            return _real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=patched_import):
            result = desktop.get_system_info()

        assert "Windows" in result
        assert "AMD64" in result
        assert "25.0%" in result
        assert "8 cores" in result
        assert "60.0%" in result
        assert "45.0%" in result
        assert "100.0 MB sent" in result
        assert "500.0 MB received" in result
        assert "Uptime" in result
