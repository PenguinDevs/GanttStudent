"""
inheritance_arrows.py
Draws inheritance arrows between classes in the project view.
@jasonyi
Created 17/06/2024
"""

import math, sys
from PyQt6 import QtWidgets, QtCore, QtGui

from .config import (
    CELL_HEIGHT,
    CELL_WIDTH,
)


class Path(QtWidgets.QGraphicsPathItem):
    def __init__(self, source: QtCore.QPointF = None, destination: QtCore.QPointF = None, *args, **kwargs):
        super(Path, self).__init__(*args, **kwargs)

        # Set endpoints.
        self._source_point = source
        self._destination_point = destination

        # Set arrow head properties.
        self._arrow_height = 5
        self._arrow_width = 4

    def set_source(self, point: QtCore.QPointF):
        """
        Set the source point of the path.

        Args:
            point (QtCore.QPointF): The source point.
        """
        self._source_point = point

    def set_destination(self, point: QtCore.QPointF):
        """
        Set the destination point of the path.

        Args:
            point (QtCore.QPointF): The destination point.
        """
        self._destination_point = point
    
    def square_path(self):
        """
        Returns a right-angled path between the source and destination points.
        """
        s = self._source_point
        d = self._destination_point

        path = QtGui.QPainterPath(QtCore.QPointF(s.x(), s.y()))
        # path.lineTo(d.x(), 0)
        path.lineTo(s.x(), d.y())
        path.lineTo(d.x(), d.y())

        return path
    
    def calculate_arrow(self, start_point=None, end_point=None):
        """
        Calculates the arrow head at the end of the path.
        """
        try:
            start_point, end_point = start_point, end_point

            if start_point is None:
                start_point = self._source_point

            if end_point is None:
                end_point = self._destination_point

            dx, dy = start_point.x() - end_point.x(), start_point.y() - end_point.y()

            leng = math.sqrt(dx ** 2 + dy ** 2)
            norm_x, norm_y = dx / leng, dy / leng  # normalize

            norm_x = 0
            norm_y = -1

            # perpendicular vector
            perp_x = -norm_y
            perp_y = norm_x

            left_x = end_point.x() + self._arrow_height * norm_x + self._arrow_width * perp_x
            left_y = end_point.y() + self._arrow_height * norm_y + self._arrow_width * perp_y

            right_x = end_point.x() + self._arrow_height * norm_x - self._arrow_width * perp_x
            right_y = end_point.y() + self._arrow_height * norm_y - self._arrow_width * perp_y

            point2 = QtCore.QPointF(left_x, left_y)
            point3 = QtCore.QPointF(right_x, right_y)

            return QtGui.QPolygonF([point2, end_point, point3])

        except (ZeroDivisionError, Exception):
            return None

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.pen().setWidth(2)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

        path = self.square_path()
        painter.drawPath(path)
        self.setPath(path)

        triangle_source = self.calculate_arrow(path.pointAtPercent(0.1), self._source_point)  # change path.PointAtPercent() value to move arrow on the line

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)

class ViewPort(QtWidgets.QGraphicsView):
    def __init__(self):
        super(ViewPort, self).__init__()

        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self._is_drawing_path = False
        self._current_path = None

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self._is_drawing_path = True
            self._current_path = Path(source=pos, destination=pos)
            self.scene().addItem(self._current_path)

            return

        super(ViewPort, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())

        if self._is_drawing_path:
            self._current_path.set_destination(pos)
            self.scene().update(self.sceneRect())
            return

        super(ViewPort, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        pos = self.mapToScene(event.pos())

        if self._is_drawing_path:
            self._current_path.set_destination(pos)
            self._is_drawing_path = False
            self._current_path = None
            self.scene().update(self.sceneRect())
            return

        super(ViewPort, self).mouseReleaseEvent(event)
    
class Arrow():
    def __init__(self, parent: QtWidgets.QWidget):
        self._scene = QtWidgets.QGraphicsScene()
        self._view = QtWidgets.QGraphicsView(self._scene)
        self._parent = parent

    def set_source_destination(self, source_row: int, source_column: int, destination_row: int, destination_column: int):
        self._source_row = source_row
        self._source_column = source_column

        self._destination_row = destination_row
        self._destination_column = destination_column

        self._row_span = self._destination_row - self._source_row
        self._column_span = self._destination_column - self._source_column

        self._draw()

    def _draw(self):
        try:
            self._scene.clear()

            path = Path()
            path._source_point = QtCore.QPointF()
            path._source_point.setX((CELL_WIDTH*(self._column_span-1)) + CELL_WIDTH//2)
            path._source_point.setY(CELL_HEIGHT*self._row_span)
            path._destination_point = QtCore.QPointF()
            path._destination_point.setX(0)
            path._destination_point.setY(CELL_HEIGHT//2)
            self._scene.addItem(path)

            self._view.setMaximumSize(CELL_WIDTH*self._column_span, CELL_HEIGHT*self._row_span)
            self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setStyleSheet("background: transparent; border: none;")
            self._view.setSceneRect(0, 0, CELL_WIDTH*self._column_span, CELL_HEIGHT*self._row_span)
            self._parent.layout().addWidget(self._view, self._source_row, self._source_column+1, self._row_span, self._column_span)
        except Exception as e:
            print(f"Failed to draw arrow: {e}")

        self._view.show()
