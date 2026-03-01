import pytest

from windows_mcp.tree.views import BoundingBox, Center, TreeElementNode, ScrollElementNode
from windows_mcp.desktop.views import Window, Status, DesktopState


@pytest.fixture
def sample_bounding_box():
    return BoundingBox(left=100, top=50, right=300, bottom=150, width=200, height=100)


@pytest.fixture
def sample_center():
    return Center(x=200, y=100)


@pytest.fixture
def sample_tree_element_node(sample_bounding_box, sample_center):
    return TreeElementNode(
        bounding_box=sample_bounding_box,
        center=sample_center,
        name="OK",
        control_type="Button",
        window_name="Notepad",
        value="",
        shortcut="Alt+O",
        xpath="/Pane/Button",
        is_focused=True,
    )


@pytest.fixture
def sample_scroll_element_node(sample_bounding_box, sample_center):
    return ScrollElementNode(
        name="Document",
        control_type="Pane",
        xpath="/Pane/ScrollViewer",
        window_name="Notepad",
        bounding_box=sample_bounding_box,
        center=sample_center,
        horizontal_scrollable=False,
        horizontal_scroll_percent=0.0,
        vertical_scrollable=True,
        vertical_scroll_percent=42.5,
        is_focused=False,
    )


@pytest.fixture
def sample_window(sample_bounding_box):
    return Window(
        name="Untitled - Notepad",
        is_browser=False,
        depth=0,
        status=Status.NORMAL,
        bounding_box=sample_bounding_box,
        handle=12345,
        process_id=6789,
    )


@pytest.fixture
def sample_desktop_state(sample_window):
    return DesktopState(
        active_desktop={"name": "Desktop 1", "id": "abc-123"},
        all_desktops=[
            {"name": "Desktop 1", "id": "abc-123"},
            {"name": "Desktop 2", "id": "def-456"},
        ],
        active_window=sample_window,
        windows=[sample_window],
    )
