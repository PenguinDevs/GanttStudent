"""
timeline.py
The timeline grid widget for the project timeline view.
@jasonyi
Created 11/06/2024
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import (
    QPixmap,
    QDrag,
    QDragMoveEvent,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDropEvent,
    QMouseEvent,
)
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton

from .config import (
    CELL_HEIGHT,
    CELL_WIDTH,
    EVEN_COLUMN_COLOUR,
    ODD_COLUMN_COLOUR,
)
if TYPE_CHECKING:
    from projects.view.task_items import TimelineTaskItem, TimelineMilestoneItem

def set_timeline_objects(task, milestone) -> None:
    global TimelineTaskItem
    global TimelineMilestoneItem
    TimelineTaskItem = task
    TimelineMilestoneItem = milestone


class TimelineGridWidget(QWidget):
    """
    A widget for the timeline grid. This is where the tasks and milestones are
    placed on the timeline.
    """

    # Maximum number of rows in the grid. This is used for the drag indicator to
    # know how many rows there are in the timeline, and disallow dragging to a
    # row that extends beyond the last row.
    max_rows = 1

    # Signal for when the grid is updated.
    grid_updated = pyqtSignal(list)

    # Signal for when a task dependency is updated.
    dependency_updated = pyqtSignal(list)

    # Signal for when tasks are updated.
    tasks_updated = pyqtSignal(list)

    # Signal for to hide/show arrows.
    hide_arrows = pyqtSignal(list)
    show_arrows = pyqtSignal(list)

    # The previous mouse buttons held down when dragging.
    _prev_buttons = None

    # Row and column mapping to the task item.
    row_column_task_mapping = {}

    # All dependencies for each task.
    all_dependencies = {}

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__()

        # This is a required behaviour to allow drag and drop
        # functionality.
        self.setAcceptDrops(True)

        # Setup the grid layout.
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.grid_layout)

        self.tasks_updated.connect(self._on_tasks_updated)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _on_tasks_updated(self, data: list) -> None:
        """
        Update the row and column mapping to each task item.
        """
        self._tasks = data[0]
        self.update_row_column_task_mapping(data)
        self.update_all_dependencies(data)

    def update_row_column_task_mapping(self, data: list = None) -> None:
        """
        Update the row and column mapping to each task item.
        """
        self.row_column_task_mapping = {}
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            widget_row, widget_column, _, days = self.grid_layout.getItemPosition(i)
            for j in range(days):
                self.row_column_task_mapping[f"{widget_row}:{widget_column+j}"] = widget

    def update_all_dependencies(self, data: list) -> None:
        """
        Update all the dependencies for each task.
        """
        self.all_dependencies.clear()
        
        tasks = data[0]
        def recursive_add_dependencies(task_uuid: str, dependencies: list) -> None:
            if task_uuid in tasks.keys():
                for dependency in tasks[task_uuid]["dependencies"]:
                    dependencies.add(dependency)
                    recursive_add_dependencies(dependency, dependencies)
        
        for task_uuid in tasks:
            dependencies = set()
            recursive_add_dependencies(task_uuid, dependencies)
            self.all_dependencies[task_uuid] = dependencies

    def setup_drag_indicator(self) -> None:
        """
        Setup the drag target indicator for the timeline grid.

        This is used to indicate where the task or milestone will be placed when
        dragged.
        """
        self._drag_target_indicator = DragTargetIndicator()
        self.grid_layout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()

        self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = None, None
    
    def decorate_drag_indicator(self, colour: str) -> None:
        """
        Decorate the drag target indicator with a colour.

        Args:
            colour (str): The colour to decorate the drag target indicator with.
        """
        self._drag_target_indicator.setStyleSheet(f"QLabel {{ background-color: {colour}; }}")

    def dragEnterEvent(self, drag_event: QDragEnterEvent) -> None:
        """
        A callback function for when a drag begins.

        This is used to assign the original dimensions of the widget being
        dragged, and to show this size on the drag target indicator.
        """
        self.hide_arrows.emit([])
        self._widget = drag_event.source()
        _, _, self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = self.grid_layout.getItemPosition(self.grid_layout.indexOf(drag_event.source()))

        drag_event.accept()

    def dragLeaveEvent(self, drag_event: QDragLeaveEvent) -> None:
        """
        A callback function for when a drag stops.

        This is used to hide the drag target indicator and reset the original
        dimensions of the widget being dragged.
        """
        self.show_arrows.emit([])
        self._drag_target_indicator.hide()

        self._widget = None
        self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = None, None

        drag_event.accept()

    def dragMoveEvent(self, drag_event: QDragMoveEvent) -> None:
        """
        A callback function for when a drag moves.

        This is used to move the drag target indicator to the correct location
        on the timeline grid.
        """
        self._prev_buttons = drag_event.buttons()
        if self._prev_buttons == Qt.MouseButton.LeftButton:
            # Find the correct location of the drop target.
            row, column = self._find_drop_location(drag_event)
            cell_height, cell_width = self._drag_target_indicator.get_cell_size()

            # Offset is for when the user drags the task item of length more than 1
            # at a point that is not the start of the task item.
            offset_cells_column = 0

            if isinstance(self._widget, DragItem):
                offset_cells_column = 0 - (self._widget.offset.x() // CELL_WIDTH)

            if not row is None and not column is None and not cell_height is None and not cell_width is None:
                new_row = max(self._widget.min_row, min(self.max_rows, row))
                new_column = max(self._widget.min_column, column+offset_cells_column)

                for dependency in self.all_dependencies[self._widget.task_uuid]:
                    if self._tasks[dependency]["row"] == new_row-1:
                        # Cannot place the task item on the same row as its dependency.
                        return

                # Inserting item into the grid also updates its position even if its
                # already in the layout.
                self.grid_layout.addWidget(
                    self._drag_target_indicator,
                    new_row,
                    new_column,
                    cell_height,
                    cell_width
                )

                # Hide the item being dragged.
                drag_event.source().hide()

                # Show the target.
                self._drag_target_indicator.show()
        
        drag_event.accept()

    def dropEvent(self, drop_event: QDropEvent) -> None:
        """
        This is a callback function for when a drag item is dropped by releasing
        it with the mouse.

        This is used to place the item in the correct location on the timeline
        grid.
        """
        self.show_arrows.emit([])
        if self._prev_buttons == Qt.MouseButton.LeftButton:
            # Use drop target location for destination, then hide it.
            row, column, cell_height, cell_width = self.grid_layout.getItemPosition(self.grid_layout.indexOf(self._drag_target_indicator))
            self._drag_target_indicator.hide()
            
            if not row is None and not column is None and not cell_height is None and not cell_width is None and not self._widget is None:
                # Inserting item into the grid also updates its position even if its
                # already in the layout.
                self.grid_layout.addWidget(self._widget, row, column, cell_height, cell_width)
                self._widget.show()

                # Fire signal for grid update.
                self.grid_updated.emit([self._widget, row, column, cell_height, cell_width])

                # Update the grid.
                self.grid_layout.activate()
        elif self._prev_buttons == Qt.MouseButton.RightButton:
            # The user is holding down the right mouse button to create an arrow.
            position = drop_event.position()
            row = int(position.y() // CELL_HEIGHT)
            column = int(position.x() // CELL_WIDTH)
            
            destination = self.row_column_task_mapping.get(f"{row}:{column}")
            if destination:
                if not isinstance(destination, TimelineTaskItem) and not isinstance(destination, TimelineMilestoneItem):
                    return
                
                source = self._widget

                # Update the destination's inheritance to source.
                self.dependency_updated.emit([source, destination])

        drop_event.accept()

    def _find_drop_location(self, drag_event: QDragMoveEvent) -> tuple:
        """
        Find the drop location of the drag event.

        Args:
            drag_event (QDragMoveEvent): The drag event object.

        Returns:
            tuple: The row and column of the drop location in terms of the grid
                position.
        """
        position = drag_event.position()
        spacing = self.grid_layout.spacing() / 2

        # Find the row and column of the drop target.
        # We use the position of the drag event to determine this.
        # We add half the spacing to the position to ensure the item is
        # placed in the correct column.
        # Row cannot be less than 1, as the date label row is at the top.
        row = max(1, int(position.y() // (CELL_HEIGHT + spacing)))
        column = int(position.x() // (CELL_WIDTH + spacing))

        return row, column

    def add_item(self, item: QWidget, row: int = 1, column: int = 1, cell_height: int = 1, cell_width: int = 1) -> None:
        """
        Add a new item to the timeline grid.

        Args:
            item (QWidget): The item to add to the timeline grid.
            row (int, optional): The initial row position. Defaults to 1.
            column (int, optional): The initial column position. Defaults to 1.
            cell_height (int, optional): The initial height of the item. Defaults to 1.
            cell_width (int, optional): The initial width of the item. Defaults to 1.
        """
        self.grid_layout.addWidget(item, row, column, cell_height, cell_width)

        if isinstance(item, TimelineMilestoneItem):
            # The TimelineMilestoneItem is a special case where the background
            # colour must be set to match with the alternating background
            # colours of the timeline grid.
            if column % 2 == 0:
                item.set_background_colour(EVEN_COLUMN_COLOUR)
            else:
                item.set_background_colour(ODD_COLUMN_COLOUR)

class DragTargetIndicator(QLabel):
    """
    A drag target indicator for the timeline grid. This is used to indicate
    where the task or milestone will be placed when dragged.
    """

    def __init__(self, parent = None) -> None:
        """Class initialisation."""
        super().__init__(parent)

        self._cell_height, self._cell_width = None, None

        self.setStyleSheet("border: 4px solid #ffffff; border-radius: 7px;")
        self.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)

    def get_cell_size(self) -> tuple:
        """
        Get the cell size of the drag target indicator.

        Returns:
            tuple: The cell height and cell width of the drag target indicator.
        """
        return self._cell_height, self._cell_width

POS_LEFT, POS_RIGHT = 1, 2
POS_TOP, POS_BOTTOM = 4, 8
POS_TOP_LEFT = POS_TOP|POS_LEFT
POS_TOP_RIGHT = POS_TOP|POS_RIGHT
POS_BOTTOM_RIGHT = POS_BOTTOM|POS_RIGHT
POS_BOTTOM_LEFT = POS_BOTTOM|POS_LEFT
class DragItem(QPushButton):
    # This is used for the size of the resize handles.
    resize_margin = 4

    # The minimum row and column that this item can be at. Influenced by its
    # dependency tasks.
    min_row = 0
    min_column = 0

    sections = [x|y for x in (POS_LEFT, POS_RIGHT) for y in (POS_TOP, POS_BOTTOM)]

    # Cursor icons.
    cursors = {
        POS_LEFT: QtCore.Qt.CursorShape.SizeHorCursor, 
        POS_RIGHT: QtCore.Qt.CursorShape.SizeHorCursor, 
    }
    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        # Used for determining the drag direction and size.
        self._start_pos = self.section = None

        # These are used for detecting where the cursor is to update the cursor
        # icon.
        self.rects = {section:QtCore.QRect() for section in self.sections}

        # This is used to calculate offset_cells_column in
        # TimelineGridWidget.dragMoveEvent().
        self.offset = None

        self.parent_widget = self.parentWidget()

        if isinstance(self, TimelineMilestoneItem):
            # Milestone cannot be resized.
            self.cursors = {}

        # Mandatory for cursor updates.
        self.setMouseTracking(True)

    def _resize_item(self, x_delta: int, is_left: bool) -> None:
        """
        Resize the item horizontally.

        Args:
            x_delta (int): The change in x position from the cursor to the where
                the cursor was first held down relative to the item. This is a
                positive value when the cursor moves away on the side of the item
                that is being resized as indicated by the is_left argument.
            is_left (bool): Whether the resize is from the left, or right if
                false.
        """
        if not self._original_cell_height or not self._original_cell_width:
            return

        row, column, _, _ = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))

        if is_left:
            # Handle resizing from the left.
            new_cell_width = x_delta // CELL_WIDTH
            # Ignore if the user attempts to resize a side that is opposite to
            # the side that is being resized.
            if new_cell_width < 0 and self._original_cell_width <= 1:
                return
            
            if column - new_cell_width < self.min_column:
                return

            self.parent_widget.grid_layout.addWidget(self, row, column - new_cell_width, self._original_cell_height, self._original_cell_width + new_cell_width)
            
            # Because the task item also moves with the cursor, thus moving the
            # origin i.e. the point where the mouse was first held down, the
            # ._original_cell_width is also updated to compensate for this.
            if new_cell_width > 0:
                self._original_cell_width += 1
            elif new_cell_width < 0:
                self._original_cell_width -= 1
        else:
            # Handle resizing from the right.
            new_cell_width = x_delta // CELL_WIDTH + self._original_cell_width

            # Ignore if the user attempts to resize a side that is opposite to
            # the side that is being resized.
            if new_cell_width <= 0:
                new_cell_width = 1
            
            self.parent_widget.grid_layout.addWidget(self, row, column, self._original_cell_height, new_cell_width)

    def mouseMoveEvent(self, mouse_event: QMouseEvent) -> None:
        """
        A callback function for when the mouse moves while the mouse is hovering
        over the widget.
        """
        if not self._start_pos is None:
            # If ._start_pos is not None, then the user is resizing the item.
            # Handle the resize logic here.

            delta = mouse_event.pos() - self._start_pos
            is_left = False
            if self.section & POS_LEFT:
                delta.setX(-delta.x())
                is_left = True
            elif not self.section & (POS_LEFT|POS_RIGHT):
                delta.setX(0)
            if self.section & POS_TOP:
                delta.setY(-delta.y())
            elif not self.section & (POS_TOP|POS_BOTTOM):
                delta.setY(0)

            self._resize_item(delta.x(), is_left)
        elif not mouse_event.buttons():
            # The user is not pressing on any mouse buttons.
            # Update the cursor shape on hover.
            self.updateCursor(mouse_event.pos())
        elif mouse_event.buttons() == Qt.MouseButton.LeftButton:
            # The user is holding down to drag and is moving the item.
            # This is only executed once each drag.
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            # Render at x2 pixel ratio to avoid blur on Retina screens.
            pixmap = QPixmap(self.size().width() * 2, self.size().height() * 2)
            pixmap.setDevicePixelRatio(2)
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)

            self.show() # Show this widget again, if it's dropped outside.
        elif mouse_event.buttons() == Qt.MouseButton.RightButton:
            # The user is holding down the right mouse button after right
            # holding on the widget.
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            drag.exec(Qt.DropAction.MoveAction)

        if isinstance(self, TimelineTaskItem):
            self.reset_style_sheet()
        elif isinstance(self, TimelineMilestoneItem):
            _, column, _, _ = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))
            if column % 2 == 0:
                self.set_background_colour(EVEN_COLUMN_COLOUR)
            else:
                self.set_background_colour(ODD_COLUMN_COLOUR)

        super().mouseMoveEvent(mouse_event)
        self.update()
    
    def updateCursor(self, position: QtCore.QPoint) -> None:
        """
        Update the cursor icon based on the position of the cursor relative to
        this item.
        """
        for section, rect in self.rects.items():
            if position in rect and not self.cursors.get(section) is None:
                # This is the section where the cursor is hovering over.
                self.setCursor(self.cursors[section])
                self.section = section
                return section
        # self.unsetCursor()
        self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, mouse_event: QMouseEvent) -> None:
        """
        A callback function for when the mouse is pressed on the widget.
        """
        self.offset = mouse_event.pos()

        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.updateCursor(mouse_event.pos()):
                # The user is resizing the item with the left mouse button held
                # down.
                self._start_pos = mouse_event.pos()
                _, _, self._original_cell_height, self._original_cell_width = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))
                return
        super().mousePressEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        """
        A callback function for when a mouse button is released while hovering
        the widget.
        """
        super().mouseReleaseEvent(mouse_event)
        self.updateCursor(mouse_event.pos())
        self._start_pos = self.section = None

        row, column, cell_height, cell_width = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))

        # The item's position or size may have changed, thus fire the grid
        # updated signal.
        self.parent_widget.grid_updated.emit([self, row, column, cell_height, cell_width])

    def resizeEvent(self, mouse_event: QMouseEvent) -> None:
        """
        Called when the widget is resized.
        
        Updates the regions for the resize handles.
        """
        super().resizeEvent(mouse_event)
        outRect = self.rect()
        inRect = self.rect().adjusted(self.resize_margin, self.resize_margin, -self.resize_margin, -self.resize_margin)
        self.rects[POS_LEFT] = QtCore.QRect(outRect.left(), inRect.top(), self.resize_margin, inRect.height())
        self.rects[POS_RIGHT] = QtCore.QRect(inRect.right(), self.resize_margin, self.resize_margin, inRect.height())
