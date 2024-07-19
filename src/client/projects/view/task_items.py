"""Stores the task items for the timeline grid."""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QMouseEvent,
    QPainter,
    QPolygon,
    QPaintEvent,
    QBrush,
    QColor,
    QPen
)

from projects.view.timeline import DragItem
from .config import (
    CELL_HEIGHT,
    CELL_WIDTH,
)

class TimelineTaskItem(DragItem):
    """A task item for the timeline grid."""

    def __init__(self, task_uuid: str, task_name: str, colour: str, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self.task_uuid = task_uuid
        self.set_name(task_name)
        self.set_colour(colour)
        
        self.reset_style_sheet()
        self.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)

    def reset_style_sheet(self) -> None:
        """Reset the style sheet of the task item."""
        self.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px solid #000000;
                border-radius: 7px;
                background-color: rgba({self._colour_r}, {self._colour_g}, {self._colour_b}, 200);
            }}

            QPushButton:hover {{
                border: 2px solid #000000;
                border-radius: 7px;
                background-color: rgba({self._colour_r}, {self._colour_g}, {self._colour_b}, 255);
            }}
            """
        )
    
    def mousePressEvent(self, mouse_event: QMouseEvent) -> None:
        """A callback function for when the mouse is pressed on the widget."""
        self.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px solid #000000;
                border-radius: 0px;
                background-color: rgba({self._colour_r}, {self._colour_g}, {self._colour_b}, 200);
            }}

            QPushButton:hover {{
                border: 2px solid #000000;
                border-radius: 0px;
                background-color: rgba({self._colour_r}, {self._colour_g}, {self._colour_b}, 255);
            }}
            """
        )

        super().mousePressEvent(mouse_event)

    def set_colour(self, colour: str) -> None:
        """
        Set the colour of the task item.

        Args:
            colour (str): The colour of the task item.
        """
        self._colour = QColor(colour)
        self._colour_r, self._colour_g, self._colour_b = self._colour.red(), self._colour.green(), self._colour.blue()
        self.reset_style_sheet()

    def set_name(self, name: str) -> None:
        """
        Set the name of the task item.

        Args:
            name (str): The name of the task item.
        """
        self._task_name = name
        self.setToolTip(name)

    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        """Called when the mouse button is released."""
        self.reset_style_sheet()

        super().mouseReleaseEvent(mouse_event)

class TimelineMilestoneItem(DragItem):
    """A milestone item for the timeline grid."""

    def __init__(self, task_uuid: str, task_name: str, colour: str, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self.task_uuid = task_uuid
        self._task_name = task_name
        self._colour = colour
        
        self.set_background_colour("#1e2749")
        self.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)
        self.setToolTip(task_name)

    def set_background_colour(self, colour: str) -> None:
        """
        Set the background colour of the milestone item.
        
        Args:
            colour (str): The colour to set the background to.
        """
        self.setStyleSheet(
            f"""
            background: {colour};
            """
        )

    def paintEvent(self, paint_event: QPaintEvent) -> None:
        """A callback function for when the widget is painted."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define the points for a diamond shape based on the button's current size
        horizontal_margin = (CELL_WIDTH - CELL_HEIGHT) // 2
        points = [
            QPoint(self.width() // 2, 0), # Top point.
            QPoint(self.width() - horizontal_margin, self.height() // 2), # Right point.
            QPoint(self.width() // 2, self.height()), # Bottom point.
            QPoint(horizontal_margin, self.height() // 2) # Left point.
        ]
        
        # Set the pen to transparent to remove the outline
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        
        # Draw the diamond shape with a specific color
        polygon = QPolygon(points)
        painter.setBrush(QBrush(QColor(self._colour)))  # Set the brush to a specific color
        painter.drawPolygon(polygon)

        # Set the pen for the text
        painter.setPen(self.palette().buttonText().color())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

    def set_colour(self, colour: str) -> None:
        """
        Set the colour of the milestone item.

        Args:
            colour (str): The colour of the milestone item.
        """
        self._colour = colour
        self.update()

    def set_name(self, name: str) -> None:
        """
        Set the name of the milestone item.

        Args:
            name (str): The name of the milestone item.
        """
        self._task_name = name
        self.setToolTip(name)
