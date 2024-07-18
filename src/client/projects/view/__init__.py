"""Projects navigation module."""

import os
from datetime import datetime, timedelta, timezone

import PyQt6.QtCore as QtCore
from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import Qt, QUrl, QMimeData, pyqtSignal
from PyQt6.QtGui import QAction, QPixmap, QDrag, QDragMoveEvent, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent, QPainter, QBrush, QPen
from PyQt6.QtWidgets import QWidget, QMenuBar, QLabel, QFrame, QGridLayout

from .task_edit import TaskEditWindow, TaskEditController

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog, create_text_input_dialog

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_projects")

TEMPLATE_ROWS = 30
CELL_WIDTH = 80
CELL_HEIGHT = 35

class ProjectViewPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\project_view_page.ui")

    def __init__(self) -> None:
        super().__init__()

        self._setup_drag_area()

    def _setup_drag_area(self) -> None:
        self.drag_area = DragWidget(self)
        self.timeline_scroll_area.layout().addWidget(self.drag_area, 0, 0)

    def setup_timeline_dates(self, start_date: datetime, end_date: datetime) -> None:
        total_columns = (end_date - start_date).days + 1

        for day in range(total_columns):
            day_label = QLabel(self)
            day_label.setText((start_date + timedelta(days=day)).strftime("%d %b"))
            day_label.setStyleSheet(
                """
                border: 2px solid #979ea8;
                background: #0f1425;
                color: #ffffff;
                qproperty-alignment: AlignCenter;
                """
            )
            day_label.setMaximumSize(CELL_WIDTH, CELL_HEIGHT)
            day_label.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)

            self.drag_area.layout().addWidget(day_label, 0, day)
        

    def setup_timeline(self, start_date: datetime, end_date: datetime) -> None:
        total_columns = (end_date - start_date).days + 1

        for i in range(total_columns):
            column_frame = QFrame(self)
            if i % 2 == 0:
                column_frame.setStyleSheet("background: #0f1425;")
            else:
                column_frame.setStyleSheet("background: #222b4e;")

            self.drag_area.layout().addWidget(column_frame, 1, i, 100, 1)

        for i in range(TEMPLATE_ROWS):
            row_label = QLabel(self)
            row_label.setText(f"Row {i}")
            row_label.setStyleSheet(
                """
                background: #0f1425;
                """
            )
            row_label.setMaximumSize(80, 35)
            row_label.setMinimumSize(80, 35)

            self.drag_area.layout().addWidget(row_label, i, 0)

    def _load_ui(self) -> QWidget:
        widget = super()._load_ui()

        self.menu_bar = QMenuBar(widget)

        self.file_menu = self.menu_bar.addMenu('&File')

        self.close_action = QAction()
        self.close_action.setText('Close')
        self.file_menu.addAction(self.close_action)

        self.file_menu.addSeparator()

        self.logout_action = QAction()
        self.logout_action.setText('Log out')
        self.file_menu.addAction(self.logout_action)

        self.exit_action = QAction()
        self.exit_action.setText('Exit')
        self.file_menu.addAction(self.exit_action)

        self.edit_menu = self.menu_bar.addMenu('&Edit')

        self.undo_action = QAction()
        self.undo_action.setText('Undo')
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QAction()
        self.redo_action.setText('Redo')
        self.edit_menu.addAction(self.redo_action)

        self.edit_menu.addSeparator()

        self.create_menu = self.edit_menu.addMenu('&Create')

        self.new_task_action = QAction()
        self.new_task_action.setText('New task')
        self.create_menu.addAction(self.new_task_action)

        self.new_milestone_action = QAction()
        self.new_milestone_action.setText('New milestone')
        self.create_menu.addAction(self.new_milestone_action)

        return widget
class ProjectViewController(BaseController):
    """Project view controller class."""

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self.task_edit_window = TaskEditWindow(self._view)
        self.task_edit_controller = TaskEditController(self._client, self.task_edit_window)

        self.reset()

    def _setup_endpoints(self) -> None:
        self._new_task = QNetworkRequest()
        self._new_task.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/task/fetch-all"))
        self._new_task.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    
    def _handle_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        A callback function for handling errors that occur from any of the
        endpoints in this controller.

        Args:
            reply (QNetworkReply): The reply object from the server.
            error (QNetworkReply.NetworkError): The network error object from the
                reply.
        """
        if error is QNetworkReply.NetworkError.ContentGoneError:
            self._client.logout()
            create_message_dialog(self._view, "Session expired", "Your session has expired. Please log in again.").exec()
            return
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            create_message_dialog(self._view, "Error", get_json_from_reply(reply)["message"]).exec()
        elif error is QNetworkReply.NetworkError.ContentNotFoundError:
            create_message_dialog(self._view, "Error", "The project could not be found.").exec()
            self._client.main_window.navigation_controller.show()
        elif error is QNetworkReply.NetworkError.ContentAccessDenied:
            create_message_dialog(self._view, "Error", "You don't have access to this project.").exec()
            self._client.main_window.navigation_controller.show()
        else:
            create_message_dialog(self._view, "Error", "An error occurred. Please try again.").exec()

    def _on_fetch_completion(self, reply: QNetworkReply) -> None:
        """
        A callback function for when the projects have been fetched.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)
        self._tasks = payload["tasks"]
        self.render()

    def fetch_tasks(self) -> None:
        """
        Fetch all tasks for the project.
        """
        reply: QNetworkReply = self._client.network_manager.post(
            self._new_task,
            to_json_data(
                {
                    "project_uuid": self._project_data["_id"],
                    "access_token": self._client.cache["access_token"]
                }
            )
        )
        reply.finished.connect(lambda: self._on_fetch_completion(reply))

    def _create_task_object(self, task_type: str) -> None:
        """
        Create a task object from the task data.

        Args:
            task_data (dict): The task data to create the task object from.
        """
        self.task_edit_controller.reset(task_type)
        self.task_edit_window.show()

    def create_task(self) -> None:
        """
        Create a new task.
        """
        self._create_task_object("task")

    def create_milestone(self) -> None:
        """
        Create a new milestone.
        """
        self._create_task_object("milestone")

    def reset(self) -> None:
        """
        Reset the data held in the controller.
        """
        self._task_items = {}

        self._project_data = None
        self._tasks = {}

    def render(self) -> None:
        """
        Render the project view.
        """
        for task_uuid, task in self._tasks.items():
            if task_uuid not in self._task_items.keys():
                days = (datetime.fromtimestamp(task["end_date"]) - datetime.fromtimestamp(task["start_date"])).days
                self._task_items[task_uuid] = TimelineItem(task_uuid, task["name"], task["colour"], parent=self._view.drag_area)
                self._view.drag_area.add_item(self._task_items[task_uuid], 1, 1, 1, days)
                self._task_items[task_uuid].show()

    def load(self, project_data: dict) -> None:
        """
        Load the projects for the user.

        Args:
            project_data (dict): The project data to load.
        """
        self._project_data = project_data
        self._view.title.setText(project_data["name"])

        self.fetch_tasks()

        if len(self._tasks) == 0:
            earliest_task_time = datetime(*datetime.now(timezone.utc).timetuple()[:3])
            latest_task_time =  datetime(*datetime.now(timezone.utc).timetuple()[:3]) + timedelta(weeks=12)
        else:
            earliest_task_time = datetime.fromtimestamp(min([task["start_date"] for task in self._tasks.values()]))
            latest_task_time = datetime.fromtimestamp(max([task["end_date"] for task in self._tasks.values()]))
        
        self._view.setup_timeline(earliest_task_time, latest_task_time)
        self._view.drag_area.setup_drag_indicator()
        self._view.setup_timeline_dates(earliest_task_time, latest_task_time)

    def close(self) -> None:
        """
        Close the project view.
        """
        self._client.main_window.navigation_controller.show()
        self.reset()

    def _connect_signals(self) -> None:
        # Bind menu bar actions.
        self._view.logout_action.triggered.connect(self._client.logout)
        self._view.exit_action.triggered.connect(self._client.exit)

        # Bind back button.
        self._view.back_button.clicked.connect(self.close)
        self._view.close_action.triggered.connect(self.close)

        # Bind task/milestone creation events.
        self._view.new_task_action.triggered.connect(self.create_task)
        self._view.new_milestone_action.triggered.connect(self.create_milestone)
        self._view.add_task_button.clicked.connect(self.create_task)
        self._view.add_milestone_button.clicked.connect(self.create_milestone)

class DragWidget(QWidget):
    """
    Generic grid dragging handler.
    """

    grid_updated = pyqtSignal(list)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.setAcceptDrops(True)

        # Setup the grid layout.
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.grid_layout)

    def setup_drag_indicator(self) -> None:
        # Add the drag target indicator. This is invisible by default,
        # we show it and move it around while the drag is active.
        self._drag_target_indicator = DragTargetIndicator()
        self.grid_layout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()

        self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = None, None
    
    def decorate_drag_indicator(self, colour: str) -> None:
        self._drag_target_indicator.setStyleSheet(f"QLabel {{ background-color: {colour}; }}")

    def dragEnterEvent(self, drag_event: QDragEnterEvent) -> None:
        # Make the drag indicator identical to the dragging object.
        # self._drag_target_indicator.setStyleSheet(drag_event.source().styleSheet())
        
        self._widget = drag_event.source()
        _, _, self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = self.grid_layout.getItemPosition(self.grid_layout.indexOf(drag_event.source()))

        drag_event.accept()

    def dragLeaveEvent(self, drag_event: QDragLeaveEvent) -> None:
        self._drag_target_indicator.hide()

        self._widget = None
        self._drag_target_indicator._cell_height, self._drag_target_indicator._cell_width = None, None

        drag_event.accept()

    def dragMoveEvent(self, drag_event: QDragMoveEvent) -> None:
        # Find the correct location of the drop target.
        row, column = self._find_drop_location(drag_event)
        cell_height, cell_width = self._drag_target_indicator.get_cell_size()
        offset_cells_column = 0

        if isinstance(self._widget, DragItem):
            offset_cells_column = 0 - (self._widget.offset.x() // CELL_WIDTH)

        if not row is None and not column is None and not cell_height is None and not cell_width is None:
            # Inserting moves the item, even if its already in the layout.
            self.grid_layout.addWidget(
                self._drag_target_indicator,
                row,
                column+offset_cells_column,
                cell_height,
                cell_width
            )

            # Hide the item being dragged.
            drag_event.source().hide()

            # Show the target.
            self._drag_target_indicator.show()
        
        drag_event.accept()

    def dropEvent(self, drop_event: QDropEvent) -> None:
        # Use drop target location for destination, then hide it.
        row, column, cell_height, cell_width = self.grid_layout.getItemPosition(self.grid_layout.indexOf(self._drag_target_indicator))
        self._drag_target_indicator.hide()
        
        if not row is None and not column is None and not cell_height is None and not cell_width is None and not self._widget is None:
            self.grid_layout.addWidget(self._widget, row, column, cell_height, cell_width)
            self._widget.show()

            # Fire signal for grid update.
            self.grid_updated.emit([self._widget, row, column])

            # Update the grid.
            self.grid_layout.activate()

        drop_event.accept()

    def _find_drop_location(self, drag_event: QDragMoveEvent) -> tuple:
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
        self.grid_layout.addWidget(item, row, column, cell_height, cell_width)

class DragTargetIndicator(QLabel):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._cell_height, self._cell_width = None, None

        self.setContentsMargins(25, 5, 25, 5)
        self.setStyleSheet("border: 4px solid #ffffff; border-radius: 7px;")
        self.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)

    def get_cell_size(self) -> tuple:
        return self._cell_height, self._cell_width

POS_LEFT, POS_RIGHT = 1, 2
POS_TOP, POS_BOTTOM = 4, 8
POS_TOP_LEFT = POS_TOP|POS_LEFT
POS_TOP_RIGHT = POS_TOP|POS_RIGHT
POS_BOTTOM_RIGHT = POS_BOTTOM|POS_RIGHT
POS_BOTTOM_LEFT = POS_BOTTOM|POS_LEFT
class DragItem(QLabel):
    resize_margin = 4

    sections = [x|y for x in (POS_LEFT, POS_RIGHT) for y in (POS_TOP, POS_BOTTOM)]

    # Cursor icons.
    cursors = {
        POS_LEFT: QtCore.Qt.CursorShape.SizeHorCursor, 
        POS_RIGHT: QtCore.Qt.CursorShape.SizeHorCursor, 
    }
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Used for determining the drag direction and size.
        self._start_pos = self.section = None

        # These are used for detecting where the cursor is to update the cursor
        # icon.
        self.rects = {section:QtCore.QRect() for section in self.sections}

        self.offset = None
        self.parent_widget = self.parentWidget()

        # Mandatory for cursor updates.
        self.setMouseTracking(True)

    def _resize_item(self, x_delta: int, is_left: bool) -> None:
        if not self._original_cell_height or not self._original_cell_width:
            return

        row, column, _, _ = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))

        if is_left:
            new_cell_width = x_delta // CELL_WIDTH
            if new_cell_width < 0 and self._original_cell_width <= 1:
                return
            
            self.parent_widget.grid_layout.addWidget(self, row, column - new_cell_width, self._original_cell_height, self._original_cell_width + new_cell_width)
            
            if new_cell_width > 0:
                self._original_cell_width += 1
            elif new_cell_width < 0:
                self._original_cell_width -= 1
        else:
            new_cell_width = x_delta // CELL_WIDTH + self._original_cell_width
            if new_cell_width <= 0:
                new_cell_width = 1
            
            self.parent_widget.grid_layout.addWidget(self, row, column, self._original_cell_height, new_cell_width)

    def mouseMoveEvent(self, mouse_event: QMouseEvent) -> None:
        if self._start_pos is not None:
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
            # Update the cursor shape on hover.
            self.updateCursor(mouse_event.pos())
        elif mouse_event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            # Render at x2 pixel ratio to avoid blur on Retina screens.
            pixmap = QPixmap(self.size().width() * 2, self.size().height() * 2)
            pixmap.setDevicePixelRatio(2)
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)
            if isinstance(self, TimelineItem):
                self.reset_style_sheet()
            self.show() # Show this widget again, if it's dropped outside.

        super().mouseMoveEvent(mouse_event)
        self.update()
    
    def updateCursor(self, position: QtCore.QPoint) -> None:
        for section, rect in self.rects.items():
            if position in rect:
                self.setCursor(self.cursors[section])
                self.section = section
                return section
        self.unsetCursor()

    def mousePressEvent(self, mouse_event: QMouseEvent) -> None:
        self.offset = mouse_event.pos()

        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.updateCursor(mouse_event.pos()):
                self._start_pos = mouse_event.pos()
                _, _, self._original_cell_height, self._original_cell_width = self.parent_widget.grid_layout.getItemPosition(self.parent_widget.grid_layout.indexOf(self))

                return
        super().mousePressEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.updateCursor(mouse_event.pos())
        self._start_pos = self.section = None
        self.setMinimumSize(0, 0)

    def resizeEvent(self, mouse_event: QMouseEvent) -> None:
        super().resizeEvent(mouse_event)
        outRect = self.rect()
        inRect = self.rect().adjusted(self.resize_margin, self.resize_margin, -self.resize_margin, -self.resize_margin)
        self.rects[POS_LEFT] = QtCore.QRect(outRect.left(), inRect.top(), self.resize_margin, inRect.height())
        self.rects[POS_RIGHT] = QtCore.QRect(inRect.right(), self.resize_margin, self.resize_margin, inRect.height())

class TimelineItem(DragItem):
    def __init__(self, task_uuid: str, task_name: str, colour: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._task_uuid = task_uuid
        self._task_name = task_name
        self._colour = colour
        
        self.reset_style_sheet()
        self.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)
        self.setToolTip(task_name)

    def reset_style_sheet(self) -> None:
        self.setStyleSheet(
            f"""
            border: 2px solid #000000;
            border-radius: 7px;
            background: {self._colour};
            """
        )
    
    def mousePressEvent(self, mouse_event: QMouseEvent) -> None:
        self.setStyleSheet(
            f"""
            border: 2px solid #000000;
            border-radius: 0px;
            background: {self._colour};
            """
        )

        super().mousePressEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        self.reset_style_sheet()

        super().mouseReleaseEvent(mouse_event)
