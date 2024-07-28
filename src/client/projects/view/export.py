from datetime import datetime

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)
import numpy as np

HEADER_HEIGHT = 150
HEADER_POSITION = (10, 10)
HEADER_FONT_SIZE = 80
HEADER_FONT = ImageFont.truetype("arial", HEADER_FONT_SIZE)

CELL_WIDTH = 80
CELL_HEIGHT = 35
CELL_FONT_SIZE = 35
CELL_FONT = ImageFont.truetype("arial", CELL_FONT_SIZE)
CELL_BORDER_COLOUR = "#0f0f0f"

TASK_ROW_WIDTH = 100

EVEN_COLUMN_COLOUR = "#0f1425"
ODD_COLUMN_COLOUR = "#222b4e"

def export_project(project_data: dict, task_data: dict) -> None:
    project_start_date = datetime.fromtimestamp(min([task["start_date"] for task in task_data.values()]))
    project_end_date = datetime.fromtimestamp(max([task["end_date"] for task in task_data.values()]))

    # The size of the image to export.
    project_cells_h_length = (project_end_date - project_start_date).days * CELL_WIDTH
    # Height is number of tasks including the cell headers and title header.
    project_cells_v_length = CELL_HEIGHT * (len(task_data) + 1) + HEADER_POSITION[1] + HEADER_HEIGHT

    image = Image.new("RGB", (project_cells_h_length, project_cells_v_length), EVEN_COLUMN_COLOUR)
    image_draw = ImageDraw.Draw(image)

    # Headers.
    image_draw.text(HEADER_POSITION, project_data["name"], "white", HEADER_FONT)

    grid_position = (0, HEADER_POSITION[1] + HEADER_HEIGHT + 10)
    image_draw.rectangle((grid_position, np.add(grid_position, (CELL_WIDTH, CELL_HEIGHT))), ODD_COLUMN_COLOUR, CELL_BORDER_COLOUR, 100)
    image_draw.text(np.add(grid_position, (5, 0)), "Name", "white", CELL_FONT)

    image.show()
