from datetime import datetime, timedelta

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)
import numpy as np

HEADER_HEIGHT = 70
HEADER_POSITION = (20, 25)
HEADER_FONT_SIZE = 70
HEADER_FONT = ImageFont.truetype("arial", HEADER_FONT_SIZE)

CELL_WIDTH = 80
CELL_HEIGHT = 35
CELL_FONT_SIZE = 24
CELL_FONT = ImageFont.truetype("arial", CELL_FONT_SIZE)
CELL_BORDER_COLOUR = "#979ea8"
CELL_TASK_BORDER_COLOUR = "#000000"
CELL_PADDING_LEFT = 12

TASK_ROW_WIDTH = 300

EVEN_COLUMN_COLOUR = "#0f1425"
ODD_COLUMN_COLOUR = "#222b4e"

def create_cell(image_draw: ImageDraw, position: tuple, text: str, fill: str) -> None:
    """
    Create a cell in the image.

    Args:
        image_draw (ImageDraw): The image to draw on.
        position (tuple): The position of the cell.
        text (str): The text to display in the cell.
        fill (str): The colour to fill the cell with.
    """
    image_draw.rectangle([position, tuple(np.add(position, (CELL_WIDTH, CELL_HEIGHT)))] , fill=fill, outline=CELL_BORDER_COLOUR, width=2)
    image_draw.text(np.add(position, (CELL_PADDING_LEFT, 4)), text, "white", CELL_FONT)

def draw_line(image_draw: ImageDraw, start: tuple, end: tuple, colour: str) -> None:
    """
    Draw a line between two points.

    Args:
        image_draw (ImageDraw): The image to draw on.
        start (tuple): The start point of the line.
        end (tuple): The end point of the line.
        colour (str): The colour of the line.
    """
    image_draw.line([start, end], fill=colour, width=5)

def export_project(project_data: dict, tasks: dict) -> Image:
    """
    Export the project to an image.

    Args:
        project_data (dict): The project data.
        tasks (dict): The tasks in the project.

    Returns:
        Image: The image of the project.
    """
    if tasks:
        project_start_date = datetime.fromtimestamp(min([task["start_date"] for task in tasks.values()]))
        project_end_date = datetime.fromtimestamp(max([task["end_date"] for task in tasks.values()]))
    else:
        project_start_date = datetime.now()
        project_end_date = datetime.now()

    # The size of the image to export.
    days = (project_end_date - project_start_date).days
    project_cells_h_length = days * CELL_WIDTH + TASK_ROW_WIDTH + CELL_WIDTH*2
    # Height is number of tasks including the cell headers and title header.
    project_cells_v_length = CELL_HEIGHT * (len(tasks) + 1) + HEADER_POSITION[1] + HEADER_HEIGHT + 15

    image = Image.new("RGB", (project_cells_h_length, project_cells_v_length), ODD_COLUMN_COLOUR)
    image_draw = ImageDraw.Draw(image)

    # Headers.
    image_draw.text(HEADER_POSITION, project_data["name"], "white", HEADER_FONT)

    grid_position = (0, HEADER_POSITION[1] + HEADER_HEIGHT + CELL_PADDING_LEFT)
    image_draw.rectangle([grid_position, tuple(np.add(grid_position, (TASK_ROW_WIDTH, CELL_HEIGHT)))] , fill=EVEN_COLUMN_COLOUR, outline=CELL_BORDER_COLOUR, width=2)
    image_draw.text(np.add(grid_position, (10, 4)), "Name", "white", CELL_FONT)

    create_cell(image_draw, tuple(np.add(grid_position, (TASK_ROW_WIDTH, 0))), "Start", EVEN_COLUMN_COLOUR)
    create_cell(image_draw, tuple(np.add(grid_position, (TASK_ROW_WIDTH + CELL_WIDTH, 0))), "End", EVEN_COLUMN_COLOUR)

    timeline_position = (grid_position[0] + TASK_ROW_WIDTH + CELL_WIDTH*2, grid_position[1])

    for day in range(days):
        create_cell(image_draw, tuple(np.add(timeline_position, (CELL_WIDTH*day, 0))), (project_start_date + timedelta(days=day)).strftime("%d/%m"), EVEN_COLUMN_COLOUR)

    for row, task in enumerate(sorted(tasks.values(), key=lambda x: x["row"])):
        start_date = datetime.fromtimestamp(task["start_date"])
        end_date = datetime.fromtimestamp(task["end_date"])

        image_draw.rectangle([tuple(np.add(grid_position, (0, CELL_HEIGHT*(row+1)))), tuple(np.add(grid_position, (TASK_ROW_WIDTH, CELL_HEIGHT*(row+2))))] , fill=ODD_COLUMN_COLOUR, outline=CELL_BORDER_COLOUR, width=2)
        image_draw.text(np.add(grid_position, (10, 4 + CELL_HEIGHT*(row+1))), task["name"], "white", CELL_FONT)
        
        create_cell(image_draw, tuple(np.add(grid_position, (TASK_ROW_WIDTH, CELL_HEIGHT*(row+1)))),  start_date.strftime("%d/%m"), ODD_COLUMN_COLOUR)
        create_cell(image_draw, tuple(np.add(grid_position, (TASK_ROW_WIDTH + CELL_WIDTH, CELL_HEIGHT*(row+1)))), end_date.strftime("%d/%m"), ODD_COLUMN_COLOUR)
        column = (start_date - project_start_date).days

        task_length = (end_date - start_date).days
        image_draw.rounded_rectangle([tuple(np.add(tuple(np.add(timeline_position, (0, CELL_HEIGHT*(row+1)))), (CELL_WIDTH*column, 0))), tuple(np.add(timeline_position, (CELL_WIDTH*column + CELL_WIDTH*task_length, CELL_HEIGHT*(row+2))))] , fill=task["colour"], outline=CELL_TASK_BORDER_COLOUR, width=2, radius=7)                                 

    # Draw lines between the parent tasks and its children.
    for task in tasks.values():
        task_row = task["row"]
        task_column = (datetime.fromtimestamp(task["end_date"]) - project_start_date).days

        for dependency_uuid in task["dependencies"]:
            dependency = tasks[dependency_uuid]
            dependency_row = dependency["row"]
            dependency_column = (datetime.fromtimestamp(dependency["start_date"]) - project_start_date).days

            start = tuple(np.add(timeline_position, (CELL_WIDTH*dependency_column, CELL_HEIGHT*(dependency_row+1) + CELL_HEIGHT//2)))
            end = tuple(np.add(timeline_position, (CELL_WIDTH*task_column, CELL_HEIGHT*(task_row+1) + CELL_HEIGHT//2)))

            draw_line(image_draw, start, end, "black")

    return image
