import math, sys
from PyQt6 import QtWidgets, QtCore, QtGui

from .config import (
    CELL_HEIGHT,
    CELL_WIDTH,
)


class Path(QtWidgets.QGraphicsPathItem):
    def __init__(self, source: QtCore.QPointF = None, destination: QtCore.QPointF = None, *args, **kwargs):
        super(Path, self).__init__(*args, **kwargs)

        self._sourcePoint = source
        self._destinationPoint = destination

        self._arrow_height = 5
        self._arrow_width = 4

    def set_source(self, point: QtCore.QPointF):
        self._sourcePoint = point

    def set_destination(self, point: QtCore.QPointF):
        self._destinationPoint = point
    
    def square_path(self):
        s = self._sourcePoint
        d = self._destinationPoint

        path = QtGui.QPainterPath(QtCore.QPointF(s.x(), s.y()))
        # path.lineTo(d.x(), 0)
        path.lineTo(s.x(), d.y())
        path.lineTo(d.x(), d.y())

        return path
    
    def calculate_arrow(self, start_point=None, end_point=None):  # calculates the point where the arrow should be drawn

        try:
            startPoint, endPoint = start_point, end_point

            if start_point is None:
                startPoint = self._sourcePoint

            if endPoint is None:
                endPoint = self._destinationPoint

            dx, dy = startPoint.x() - endPoint.x(), startPoint.y() - endPoint.y()

            leng = math.sqrt(dx ** 2 + dy ** 2)
            normX, normY = dx / leng, dy / leng  # normalize

            normX = 0
            normY = -1

            # perpendicular vector
            perpX = -normY
            perpY = normX

            leftX = endPoint.x() + self._arrow_height * normX + self._arrow_width * perpX
            leftY = endPoint.y() + self._arrow_height * normY + self._arrow_width * perpY

            rightX = endPoint.x() + self._arrow_height * normX - self._arrow_width * perpX
            rightY = endPoint.y() + self._arrow_height * normY - self._arrow_width * perpY

            point2 = QtCore.QPointF(leftX, leftY)
            point3 = QtCore.QPointF(rightX, rightY)

            return QtGui.QPolygonF([point2, endPoint, point3])

        except (ZeroDivisionError, Exception):
            return None

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.pen().setWidth(2)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

        path = self.square_path()
        painter.drawPath(path)
        self.setPath(path)

        triangle_source = self.calculate_arrow(path.pointAtPercent(0.1), self._sourcePoint)  # change path.PointAtPercent() value to move arrow on the line

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)


class ViewPort(QtWidgets.QGraphicsView):

    def __init__(self):
        super(ViewPort, self).__init__()

        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self._isdrawingPath = False
        self._current_path = None

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self._isdrawingPath = True
            self._current_path = Path(source=pos, destination=pos)
            self.scene().addItem(self._current_path)

            return

        super(ViewPort, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):

        pos = self.mapToScene(event.pos())

        if self._isdrawingPath:
            self._current_path.set_destination(pos)
            self.scene().update(self.sceneRect())
            return

        super(ViewPort, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:

        pos = self.mapToScene(event.pos())

        if self._isdrawingPath:
            self._current_path.set_destination(pos)
            self._isdrawingPath = False
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
        self._scene.clear()

        path = Path()
        path._sourcePoint = QtCore.QPointF()
        path._sourcePoint.setX((CELL_WIDTH*(self._column_span-1)) + CELL_WIDTH//2)
        path._sourcePoint.setY(CELL_HEIGHT*self._row_span)
        path._destinationPoint = QtCore.QPointF()
        path._destinationPoint.setX(0)
        path._destinationPoint.setY(CELL_HEIGHT//2)
        self._scene.addItem(path)

        self._view.setMaximumSize(CELL_WIDTH*self._column_span, CELL_HEIGHT*self._row_span)
        self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setStyleSheet("background: transparent; border: none;")
        self._view.setSceneRect(0, 0, CELL_WIDTH*self._column_span, CELL_HEIGHT*self._row_span)
        self._parent.layout().addWidget(self._view, self._source_row, self._source_column+1, self._row_span, self._column_span)

        self._view.show()
    


def main():
    app = QtWidgets.QApplication(sys.argv)

    window = ViewPort()
    scene = QtWidgets.QGraphicsScene()
    window.setScene(scene)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()