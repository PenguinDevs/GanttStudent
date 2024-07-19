"""Projects navigation module."""

import os
from datetime import datetime, timedelta, timezone

from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import (
    QAction,
    QMouseEvent,
    QFont,
)
from PyQt6.QtWidgets import QWidget, QMenuBar, QLabel, QFrame

from .task_edit import TaskEditWindow, TaskEditController
from .timeline import TimelineGridWidget, set_timeline_objects
from .task_items import TimelineTaskItem, TimelineMilestoneItem

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog

from .config import (
    CELL_HEIGHT,
    CELL_WIDTH,
    EVEN_COLUMN_COLOUR,
    ODD_COLUMN_COLOUR,
    TEMPLATE_ROWS
)
set_timeline_objects(TimelineTaskItem, TimelineMilestoneItem)


class ProjectViewPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\project_view_page.ui")

    def __init__(self) -> None:
        """Class initialisation."""
        super().__init__()

        self._setup_drag_area()

    def assign_controller(self, controller: BaseController) -> None:
        super().assign_controller(controller)

        self.drag_area.grid_updated.connect(self._controller.grid_updated)

    def _setup_drag_area(self) -> None:
        """Setup the drag area for the timeline."""
        self.drag_area = TimelineGridWidget(self.timeline_scroll_area)
        self.timeline_scroll_area.layout().addWidget(self.drag_area, 0, 0)

    def setup_task_rows(self) -> None:
        """
        Create rows of placeholder frames to set a fixed height for each row in
        the left task list. (PyQt method).
        """
        for i in range(TEMPLATE_ROWS):
            row_label = QFrame(self)
            
            # Set a rigid size
            row_label.setMaximumSize(400, 35)
            row_label.setMinimumSize(400, 35)

            # Blend with the background
            row_label.setStyleSheet(
                """
                background: #1e2749;
                """
            )

            self.tasks_frame.layout().addWidget(row_label, i+1, 0)

    def setup_timeline_dates(self, start_date: datetime, end_date: datetime) -> None:
        """
        Create the date labels for the timeline like table headers.
        """
        # Add +1 to allow for one additional day of tasks to be assigned so that
        # the timeline can be extended.
        total_columns = (end_date - start_date).days + 1

        # Set a sont for the date labels.
        font = QFont()
        font.setBold(True)
        font.setFamily("Segoe Ui")
        font.setPixelSize(14)

        for day in range(total_columns):
            day_label = QLabel(self)
            day_label.setText((start_date + timedelta(days=day)).strftime("%d %b"))
            day_label.setStyleSheet(
                f"""
                border: 2px solid #979ea8;
                background: {EVEN_COLUMN_COLOUR};
                color: #ffffff;
                qproperty-alignment: AlignCenter;
                """
            )
            day_label.setFont(font)
            day_label.setMaximumSize(CELL_WIDTH, CELL_HEIGHT)
            day_label.setMinimumSize(CELL_WIDTH, CELL_HEIGHT)

            # Top row, in their respective column.
            self.drag_area.layout().addWidget(day_label, 0, day)

    def setup_timeline(self, start_date: datetime, end_date: datetime) -> None:
        """
        Create the two alternating shades of the background colour for the
        timeline columns in the background, repeating until the end of the
        timeline.

        Also create rows of placeholder frames to set a fixed height for each
        row in the project timeline. (PyQt method).
        """
        # Same number of columns as .setup_timeline_dates()
        total_columns = (end_date - start_date).days + 1

        # Alternating shade of the background colour for the timeline columns.
        for i in range(total_columns):
            column_frame = QFrame(self)
            if i % 2 == 0:
                # Even column
                column_frame.setStyleSheet(f"background: {EVEN_COLUMN_COLOUR};")
            else:
                # Odd column
                column_frame.setStyleSheet(f"background: {ODD_COLUMN_COLOUR};")

            self.drag_area.layout().addWidget(column_frame, 1, i, 100, 1)

        # Create rows of placeholder frames to set a fixed height for each row in
        # the project timeline.
        for i in range(TEMPLATE_ROWS):
            row_label = QLabel(self)
            row_label.setText(f"Row {i}")
            row_label.setStyleSheet(
                f"""
                background: {EVEN_COLUMN_COLOUR};
                """
            )

            # Set a rigid size.
            row_label.setMaximumSize(80, 35)
            row_label.setMinimumSize(80, 35)

            self.drag_area.layout().addWidget(row_label, i, 0)
        
    def _load_ui(self) -> QWidget:
        widget = super()._load_ui()

        # Setup the menu bar (top-left options in the window).
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

        self._task_items = {}
        self._row_items = {}

        self.reset()

    def _setup_endpoints(self) -> None:
        self._fetch_all_tasks = QNetworkRequest()
        self._fetch_all_tasks.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/task/fetch-all"))
        self._fetch_all_tasks.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    
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

        if self.start_date is None or self.end_date is None:
            # self.start_date or self.end_date are None if this is the first
            # time loading this project in this session i.e. no tasks have been
            # loaded yet.

            # Set the minimum size of the timeline to be 12 weeks from today's
            # date.
            minimim_latest = datetime(*datetime.now(timezone.utc).timetuple()[:3]) + timedelta(weeks=12)
            if len(self._tasks) == 0:
                # If no tasks, then set the start date to today's date and the
                # end date to minimim_latest.
                self.start_date = datetime(*datetime.now(timezone.utc).timetuple()[:3])
                self.end_date =  minimim_latest
            else:
                # If there are tasks, then set the start date to the earliest
                # start date of the tasks and the end date to the latest end date
                # of the tasks or minimim_latest, whichever is later.
                self.start_date = datetime.fromtimestamp(min([task["start_date"] for task in self._tasks.values()]))
                self.end_date = datetime.fromtimestamp(max([max(minimim_latest.timestamp(), task["end_date"]) for task in self._tasks.values()]))

            # Essential setup for the user-interface of the timeline.
            # Only called once for the first time the project is loaded, as the
            # start_date and end_date are set after the first time, and the
            # if statement above will not be executed again unless the project
            # is closed and re-opened.
            self._view.setup_task_rows()
            self._view.setup_timeline(self.start_date, self.end_date)
            self._view.drag_area.setup_drag_indicator()
            self._view.setup_timeline_dates(self.start_date, self.end_date)

        # Render the tasks on the timeline, whether it be on the first time, or
        # updating the tasks.
        self.render()

    def fetch_tasks(self) -> None:
        """
        Fetch all tasks for the project.
        """
        reply: QNetworkReply = self._client.network_manager.post(
            self._fetch_all_tasks,
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
        Prompt a task editing window to create a new task object (Includes both
        task and milestone, as milestones are considered a task object in this
        program).

        Args:
            task_data (dict): The task data to create the task object from.
        """
        # Clear all previous data from the task edit controller, if any.
        self.task_edit_controller.reset(task_type)

        # Show the task edit window.
        self.task_edit_window.show()

    def create_task(self) -> None:
        """
        Prompt a task editing window to create a new task.
        """
        self._create_task_object("task")

    def create_milestone(self) -> None:
        """
        Prompt a task editing window to create a new milestone.
        """
        self._create_task_object("milestone")

    def reset(self) -> None:
        """
        Reset the data held in this controller, as well as the user-interface.
        """
        # Clear data
        self._project_data = None
        self._tasks = {}
        
        self.start_date = None
        self.end_date = None

        # Clear task UI items in the timeline.
        for item in self._task_items.values():
            self._view.drag_area.grid_layout.removeWidget(item)
            item.deleteLater()
            del item
        self._task_items = {}

        # Clear task UI items in the task list (on the left).
        for item in self._row_items.values():
            self._view.tasks_frame.layout().removeWidget(item)
            item.deleteLater()
            del item
        self._row_items = {}
        
        # Clear the timeline UI object.
        item = self._view.drag_area.findChild(TimelineGridWidget)
        if item:
            self._view.timeline_scroll_area.removeWidget(item)
            item.deleteLater()
            del item

    def _get_item_double_click_callback(self, task_data: dict) -> None:
        """
        Get the callback function for when a task item is double-clicked. This
        will prompt the task edit window to edit the task.

        Args:
            task_data (dict): The task data as a dictionary object to edit.
        """

        def callback(mouse_event: QMouseEvent) -> None:
            # Clear all previous data from the task edit controller, if any.
            # Also set the task data to the task data passed in.
            # Then show the task edit window.
            self.task_edit_controller.reset(task_data["task_type"], task_data)
            self.task_edit_window.show()
        
        return callback

    def render(self) -> None:
        """
        Render the project view with the tasks and milestones as user interface
        items.

        Creates, updates, or removes task items and row items as necessary.
        """
        # Iterate every task in the project.
        for task_uuid, task in self._tasks.items():
            # Calculate the start and end column of the task for the timeline
            # grid.
            start_column = (datetime.fromtimestamp(task["start_date"]) - self.start_date).days
            end_column = (datetime.fromtimestamp(task["end_date"]) - self.start_date).days

            # If the task is outside the timeline to the left beyond the start
            # date column, then load the project again but this time with a new
            # earlier start date. See the .fetch_tasks() function for more
            # information.
            if start_column < 0:
                project_data = self._project_data
                self.reset()
                return self.load(project_data)

            # This is the number of days the task spans across i.e. length of
            # task.
            days = end_column - start_column

            if not task_uuid in self._task_items.keys():
                # If the task item does not exist, then create it.
                # Create the task/milestone object.
                class_type = TimelineMilestoneItem if task["task_type"] == "milestone" else TimelineTaskItem
                self._task_items[task_uuid] = class_type(task_uuid, task["name"], task["colour"], parent=self._view.drag_area)

                # Add this task item to the timeline grid layout.
                self._view.drag_area.add_item(self._task_items[task_uuid], task["row"]+1, start_column, 1, days)
                self._task_items[task_uuid].show()

                # Set the task item's double-click event to prompt the task edit
                # window to edit the task.
                self._task_items[task_uuid].mouseDoubleClickEvent = self._get_item_double_click_callback(task)
            else:
                # If the task item exists, then update it.
                # Update the task item's position and size in the timeline grid.
                self._view.drag_area.grid_layout.addWidget(self._task_items[task_uuid], task["row"]+1, start_column, 1, days)

                # Update the task item's name and colour.
                self._task_items[task_uuid].set_name(task["name"])
                self._task_items[task_uuid].set_colour(task["colour"])
            
            if not task_uuid in self._row_items.keys():
                # If the row item (on the left panel) does not exist, then
                # create it.
                self._row_items[task_uuid] = RowLabel(parent=self._view.drag_area)
                self._row_items[task_uuid].show()
            
            # Set the row item's task data.
            # This is applied regardless of whether the row item has been created
            # just now, or already exists.
            self._row_items[task_uuid].set_task_data(task["name"], datetime.fromtimestamp(task["start_date"]), datetime.fromtimestamp(task["end_date"]))
            self._view.tasks_frame.layout().addWidget(self._row_items[task_uuid], task["row"]+1, 0)

        # Iterate every task item in the timeline to check if any tasks have
        # been removed from the project.
        for task_uuid, item in list(self._task_items.items()):
            if not task_uuid in self._tasks.keys():
                # Delete the task item.
                self._view.drag_area.grid_layout.removeWidget(item)
                self._task_items.pop(task_uuid)
                item.deleteLater()
                del item

                # Delete the row item.
                row_item = self._row_items[task_uuid]
                row_item.deleteLater()
                self._row_items.pop(task_uuid)
                del row_item

        # Update the maximum number of rows in the drag area.
        # This is for the drag indicator to know how many rows there are in the
        # timeline, and disallow dragging to a row that extends beyond the last
        # row.
        self._view.drag_area.max_rows = len(self._tasks)

        # Ensure that the drag indicator is at the top of the z-index.
        self._view.drag_area._drag_target_indicator.raise_()

    def load(self, project_data: dict) -> None:
        """
        Load the projects for the user.

        Args:
            project_data (dict): The project data to load.
        """
        self._project_data = project_data

        # Set the title of the project view.
        self._view.title.setText(project_data["name"])

        # Fetch the tasks for the project from the server. This will also render
        # the project's UI after the tasks are fetched.
        self.fetch_tasks()

    def close(self) -> None:
        """
        Close the project view.
        """
        self._client.main_window.navigation_controller.show()
        self.reset()

    def grid_updated(self, data: list) -> None:
        """
        A callback function for when the grid is updated.

        Args:
            data (list): The data from the grid update.
                i=0: Widget object.
                i=1: New row.
                i=2: New column.
                i=3: New cell height.
                i=4: New cell width.
        """
        item, row, column, cell_height, cell_width = data
        if isinstance(item, TimelineTaskItem) or isinstance(item, TimelineMilestoneItem):
            # Obtain the task data.
            task_uuid = item.task_uuid
            task_data = self._tasks[task_uuid]

            # Calculate what the new row, start date, and end date that is to be
            # assigned should be.
            new_row = row - 1
            new_start_date = (self.start_date + timedelta(days=column)).timestamp()
            new_end_date = (self.start_date + timedelta(days=column + cell_width)).timestamp()

            if new_row == task_data["row"] and new_start_date == task_data["start_date"] and new_end_date == task_data["end_date"]:
                # No changes made, ignore.
                return

            # Search for other tasks in the same row to update their row if
            # necessary.
            for other_task in self._tasks.values():
                if other_task["row"] == row - 1 and not other_task == task_data:
                    # Switch the row of the other task to the old row of the
                    # task that was moved.
                    other_task["row"] = task_data["row"]
                    self.task_edit_controller.update_task(other_task)

                    # Break because only one task can be in the same row.
                    break
            
            # Update the task data.
            task_data["row"] = new_row
            task_data["start_date"] = new_start_date
            task_data["end_date"] = new_end_date

            self.task_edit_controller.update_task(task_data)

            self.render()

    def _on_vertical_scrollbar_updated(self, value: int) -> None:
        """
        A callback function for when the vertical scrollbar is updated.

        This function is used to sync the vertical scrollbars of the task list
        and the timeline.

        Args:
            value (int): The new value of the vertical scrollbar.
        """
        self._view.tasks.verticalScrollBar().setValue(value)
        self._view.timeline.verticalScrollBar().setValue(value)

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

        # Syncing scrollbars.
        # This is to ensure that the vertical scrollbars of the task list and
        # the timeline are in sync.
        self._view.tasks.verticalScrollBar().valueChanged.connect(self._on_vertical_scrollbar_updated)
        self._view.timeline.verticalScrollBar().valueChanged.connect(self._on_vertical_scrollbar_updated)

class RowLabel(QFrame):
    """
    A row label for the task list on the left side of the project view.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self._load_ui()

    def _load_ui(self) -> None:
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\project_view_task_item.ui"), self)
        
    def set_task_data(self, name: str, start: datetime, end: datetime) -> None:
        """
        Visually assign the task information to the row label.

        Args:
            name (str): The name of the task.
            start (datetime): The start date of the task.
            end (datetime): The end date of the task.
        """
        self.name_label.setText(name)
        self.start_label.setText(start.strftime("%d/%m"))
        self.end_label.setText(end.strftime("%d/%m"))
