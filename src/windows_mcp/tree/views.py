from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TreeState:
    root_node: "TreeElementNode" | None = None
    dom_node: "ScrollElementNode" | None = None
    interactive_nodes: list["TreeElementNode"] = field(default_factory=list)
    scrollable_nodes: list["ScrollElementNode"] = field(default_factory=list)
    dom_informative_nodes: list["TextElementNode"] = field(default_factory=list)

    def interactive_elements_to_string(
        self, coord_transform: Callable[[int, int], tuple[int, int]] | None = None
    ) -> str:
        if not self.interactive_nodes:
            return "No interactive elements"
        header = "# id|window|control_type|name|coords|focus"
        rows = [header]
        for idx, node in enumerate(self.interactive_nodes):
            coord_str = _format_center(node.center, coord_transform)
            row = f"{idx}|{node.window_name}|{node.control_type}|{node.name}|{coord_str}|{node.is_focused}"
            rows.append(row)
        return "\n".join(rows)

    def scrollable_elements_to_string(
        self, coord_transform: Callable[[int, int], tuple[int, int]] | None = None
    ) -> str:
        if not self.scrollable_nodes:
            return "No scrollable elements"
        header = "# id|window|control_type|name|coords|h_scroll|h_pct|v_scroll|v_pct|focus"
        rows = [header]
        base_index = len(self.interactive_nodes)
        for idx, node in enumerate(self.scrollable_nodes):
            coord_str = _format_center(node.center, coord_transform)
            row = (
                f"{base_index + idx}|{node.window_name}|{node.control_type}|{node.name}|"
                f"{coord_str}|{node.horizontal_scrollable}|{node.horizontal_scroll_percent}|"
                f"{node.vertical_scrollable}|{node.vertical_scroll_percent}|{node.is_focused}"
            )
            rows.append(row)
        return "\n".join(rows)


def _format_center(
    center: "Center", coord_transform: Callable[[int, int], tuple[int, int]] | None
) -> str:
    if coord_transform is None:
        return center.to_string()
    tx, ty = coord_transform(center.x, center.y)
    return f"({tx},{ty})"


@dataclass
class BoundingBox:
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int

    @classmethod
    def from_bounding_rectangle(cls, bounding_rectangle: Any) -> "BoundingBox":
        return cls(
            left=bounding_rectangle.left,
            top=bounding_rectangle.top,
            right=bounding_rectangle.right,
            bottom=bounding_rectangle.bottom,
            width=bounding_rectangle.width(),
            height=bounding_rectangle.height(),
        )

    def get_center(self) -> "Center":
        return Center(x=self.left + self.width // 2, y=self.top + self.height // 2)

    def xywh_to_string(self):
        return f"({self.left},{self.top},{self.width},{self.height})"

    def xyxy_to_string(self):
        x1, y1, x2, y2 = self.convert_xywh_to_xyxy()
        return f"({x1},{y1},{x2},{y2})"

    def convert_xywh_to_xyxy(self) -> tuple[int, int, int, int]:
        x1, y1 = self.left, self.top
        x2, y2 = self.left + self.width, self.top + self.height
        return x1, y1, x2, y2


@dataclass
class Center:
    x: int
    y: int

    def to_string(self) -> str:
        return f"({self.x},{self.y})"


@dataclass
class TreeElementNode:
    bounding_box: BoundingBox
    center: Center
    name: str = ""
    control_type: str = ""
    window_name: str = ""
    value: str = ""
    shortcut: str = ""
    xpath: str = ""
    is_focused: bool = False

    def update_from_node(self, node: "TreeElementNode"):
        self.name = node.name
        self.control_type = node.control_type
        self.window_name = node.window_name
        self.value = node.value
        self.shortcut = node.shortcut
        self.bounding_box = node.bounding_box
        self.center = node.center
        self.xpath = node.xpath
        self.is_focused = node.is_focused

    # Legacy method kept for compatibility if needed, but not used in new format
    def to_row(self, index: int):
        return [
            index,
            self.window_name,
            self.control_type,
            self.name,
            self.value,
            self.shortcut,
            self.center.to_string(),
            self.is_focused,
        ]


@dataclass
class ScrollElementNode:
    name: str
    control_type: str
    xpath: str
    window_name: str
    bounding_box: BoundingBox
    center: Center
    horizontal_scrollable: bool
    horizontal_scroll_percent: float
    vertical_scrollable: bool
    vertical_scroll_percent: float
    is_focused: bool

    # Legacy method kept for compatibility
    def to_row(self, index: int, base_index: int):
        return [
            base_index + index,
            self.window_name,
            self.control_type,
            self.name,
            self.center.to_string(),
            self.horizontal_scrollable,
            self.horizontal_scroll_percent,
            self.vertical_scrollable,
            self.vertical_scroll_percent,
            self.is_focused,
        ]


@dataclass
class TextElementNode:
    text: str


ElementNode = TreeElementNode | ScrollElementNode | TextElementNode
