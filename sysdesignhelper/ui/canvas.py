from __future__ import annotations

import math

from PyQt6 import sip
from PyQt6.QtCore import QLineF, QMimeData, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QDrag, QFont, QFontMetricsF, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF,
)
from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QGraphicsItem, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..content import Library
from ..design import MODES, PARTITIONING, PATHS, PROTOCOLS, Block, Connection, Design
from . import theme
from .widgets import label

MIME = "application/x-sysdesign-component"
BLOCK_W, BLOCK_H = 196.0, 68.0
HANDLE_R = 7.0


def block_summary(block: Block) -> str:
    parts = []
    if block.technology:
        parts.append(block.technology)
    if block.instances > 1:
        parts.append(f"x{block.instances}")
    if block.replication_factor > 1:
        parts.append(f"RF {block.replication_factor}")
    if block.partitioning != "none":
        parts.append(f"{block.partitioning} by {block.partition_key or '?'}")
    parts.extend(value for value in block.extras.values() if value)
    return "  ·  ".join(parts)


def connection_summary(connection: Connection) -> str:
    parts = [part for part in (connection.protocol, connection.label) if part]
    if connection.path != "both":
        parts.append(f"{connection.path} path")
    return "  ·  ".join(parts)


class BlockItem(QGraphicsItem):
    def __init__(self, block: Block, component_name: str, read_only: bool):
        super().__init__()
        self.block = block
        self.component_name = component_name
        self.read_only = read_only
        self.hovered = False
        self.setPos(block.x, block.y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not read_only)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not read_only)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.refresh()

    def refresh(self) -> None:
        lines = [f"{self.component_name}: {self.block.name}" if self.block.name else self.component_name]
        summary = block_summary(self.block)
        if summary:
            lines.append(summary)
        if self.block.note:
            lines.append(self.block.note)
        if self.read_only:
            lines.append("Double-click to open this Component's Page")
        self.setToolTip("\n".join(lines))
        self.update()

    def body_rect(self) -> QRectF:
        return QRectF(0, 0, BLOCK_W, BLOCK_H)

    def handle_rect(self) -> QRectF:
        return QRectF(BLOCK_W - HANDLE_R, BLOCK_H / 2 - HANDLE_R, 2 * HANDLE_R, 2 * HANDLE_R)

    def handle_scene_rect(self) -> QRectF:
        return self.mapRectToScene(self.handle_rect().adjusted(-3, -3, 3, 3))

    def center(self) -> QPointF:
        return self.mapToScene(self.body_rect().center())

    def boundingRect(self) -> QRectF:
        return self.body_rect().adjusted(-2, -2, HANDLE_R + 4, 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = self.isSelected()
        painter.setPen(QPen(QColor(theme.ACCENT if selected else theme.BORDER), 2 if selected else 1))
        painter.setBrush(QBrush(QColor(theme.RAISED)))
        painter.drawRoundedRect(self.body_rect(), 8, 8)

        text_rect = self.body_rect().adjusted(12, 7, -12, -7)
        font = QFont(painter.font())
        font.setPointSizeF(9)
        font.setCapitalization(QFont.Capitalization.AllUppercase)
        painter.setFont(font)
        painter.setPen(QColor(theme.MUTED))
        kind = QFontMetricsF(font).elidedText(self.component_name, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, kind)

        font = QFont(painter.font())
        font.setCapitalization(QFont.Capitalization.MixedCase)
        font.setPointSizeF(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(theme.TEXT))
        name = QFontMetricsF(font).elidedText(self.block.name or self.component_name,
                                               Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        font.setBold(False)
        font.setPointSizeF(10)
        painter.setFont(font)
        painter.setPen(QColor(theme.MUTED))
        summary = QFontMetricsF(font).elidedText(block_summary(self.block),
                                                  Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, summary)

        if not self.read_only and (self.hovered or selected):
            painter.setPen(QPen(QColor(theme.BG), 2))
            painter.setBrush(QBrush(QColor(theme.ACCENT)))
            painter.drawEllipse(self.handle_rect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.block.x, self.block.y = self.pos().x(), self.pos().y()
            if self.scene() is not None:
                self.scene().block_moved(self)
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event) -> None:
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event) -> None:
        self.hovered = False
        self.update()


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, connection: Connection, source: BlockItem, target: BlockItem, read_only: bool):
        super().__init__()
        self.connection = connection
        self.source = source
        self.target = target
        self.arrow = QPolygonF()
        self.label_at = QPointF()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not read_only)
        self.refresh()

    def refresh(self) -> None:
        self.setToolTip(f"{self.connection.mode}  ·  {connection_summary(self.connection)}".rstrip(" ·"))
        self.update_path()

    def update_path(self) -> None:
        self.prepareGeometryChange()
        source_center, target_center = self.source.center(), self.target.center()
        line = QLineF(source_center, target_center)
        if line.length() < 1:
            self.setPath(QPainterPath())
            return
        # Shift sideways so that A->B and B->A do not draw on top of each other,
        # then clip the shifted line to each Block's edge so the arrowhead stays visible.
        normal = line.normalVector().unitVector()
        offset = QPointF(normal.dx(), normal.dy()) * 9
        start = self._exit_point(source_center, source_center + offset, target_center + offset)
        end = self._exit_point(target_center, target_center + offset, source_center + offset)
        path = QPainterPath(start)
        path.lineTo(end)
        self.setPath(path)

        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        size = 10
        self.arrow = QPolygonF([
            end,
            end - QPointF(math.cos(angle - 0.45) * size, math.sin(angle - 0.45) * size),
            end - QPointF(math.cos(angle + 0.45) * size, math.sin(angle + 0.45) * size),
        ])
        # Off-centre only when B->A also exists, so the two labels of the pair do not collide.
        scene = self.scene()
        paired = scene is not None and any(
            c.source == self.connection.target and c.target == self.connection.source
            for c in scene.design.connections
        )
        self.label_at = start + (end - start) * (0.4 if paired else 0.5)

    @staticmethod
    def _exit_point(center: QPointF, inside: QPointF, toward: QPointF) -> QPointF:
        """Where the ray from `inside` toward `toward` leaves the Block centred on `center`."""
        dx, dy = toward.x() - inside.x(), toward.y() - inside.y()
        steps = []
        if dx:
            steps.append((center.x() + math.copysign(BLOCK_W / 2, dx) - inside.x()) / dx)
        if dy:
            steps.append((center.y() + math.copysign(BLOCK_H / 2, dy) - inside.y()) / dy)
        if not steps:
            return inside
        step = min(steps)
        return QPointF(inside.x() + dx * step, inside.y() + dy * step)

    def boundingRect(self) -> QRectF:
        return self.path().boundingRect().adjusted(-90, -24, 90, 24)

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(self.path())

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self.path().isEmpty():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(theme.ACCENT if self.isSelected() else theme.MUTED)
        pen = QPen(color, 2 if self.isSelected() else 1.5)
        if self.connection.mode == "async":
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(color))
        painter.drawPolygon(self.arrow)

        text = connection_summary(self.connection)
        if text:
            font = QFont(painter.font())
            font.setPointSizeF(9.5)
            painter.setFont(font)
            metrics = QFontMetricsF(font)
            box = metrics.boundingRect(text).adjusted(-5, -2, 5, 2)
            box.moveCenter(self.label_at)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(theme.BG)))
            painter.drawRoundedRect(box, 4, 4)
            painter.setPen(QColor(theme.TEXT if self.isSelected() else theme.MUTED))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)


class DesignScene(QGraphicsScene):
    design_changed = pyqtSignal()
    block_activated = pyqtSignal(str)

    def __init__(self, library: Library, design: Design | None = None, read_only: bool = False):
        super().__init__()
        self.library = library
        self.read_only = read_only
        self.design = Design()
        self.block_items: dict[str, BlockItem] = {}
        self.connection_items: dict[str, ConnectionItem] = {}
        self._drag_source: BlockItem | None = None
        self._drag_line = None
        self.load(design or Design())

    def load(self, design: Design) -> None:
        self.clear()
        self.block_items.clear()
        self.connection_items.clear()
        self.design = design
        for block in design.blocks:
            self._add_block_item(block)
        for connection in design.connections:
            self._add_connection_item(connection)
        self.design_changed.emit()

    def component_name(self, component_id: str) -> str:
        page = self.library.components.get(component_id)
        return page.name if page else component_id

    def add_block(self, component_id: str, pos: QPointF) -> Block:
        block = self.design.add_block(component_id, name=self.component_name(component_id),
                                      x=pos.x() - BLOCK_W / 2, y=pos.y() - BLOCK_H / 2)
        item = self._add_block_item(block)
        self.clearSelection()
        item.setSelected(True)
        self.design_changed.emit()
        return block

    def connect_blocks(self, source_id: str, target_id: str) -> Connection | None:
        connection = self.design.connect(source_id, target_id)
        if connection is None:
            return None
        item = self._add_connection_item(connection)
        self.clearSelection()
        item.setSelected(True)
        self.design_changed.emit()
        return connection

    def delete_selected(self) -> None:
        if self.read_only:
            return
        selected = self.selectedItems()
        if not selected:
            return
        for item in selected:
            if isinstance(item, ConnectionItem):
                self.design.remove_connection(item.connection.id)
        for item in selected:
            if isinstance(item, BlockItem):
                self.design.remove_block(item.block.id)
        self._rebuild()

    def clear_design(self) -> None:
        self.load(Design())

    def selected_object(self) -> Block | Connection | None:
        selected = self.selectedItems()
        if len(selected) != 1:
            return None
        item = selected[0]
        if isinstance(item, BlockItem):
            return item.block
        if isinstance(item, ConnectionItem):
            return item.connection
        return None

    def object_edited(self, target: Block | Connection) -> None:
        if isinstance(target, Block) and target.id in self.block_items:
            self.block_items[target.id].refresh()
        elif isinstance(target, Connection) and target.id in self.connection_items:
            self.connection_items[target.id].refresh()
        self.design_changed.emit()

    def block_moved(self, item: BlockItem) -> None:
        for connection_item in self.connection_items.values():
            if item in (connection_item.source, connection_item.target):
                connection_item.update_path()

    def _rebuild(self) -> None:
        design = self.design
        self.load(design)

    def _add_block_item(self, block: Block) -> BlockItem:
        item = BlockItem(block, self.component_name(block.component), self.read_only)
        self.addItem(item)
        self.block_items[block.id] = item
        return item

    def _add_connection_item(self, connection: Connection) -> ConnectionItem:
        item = ConnectionItem(connection, self.block_items[connection.source],
                              self.block_items[connection.target], self.read_only)
        self.addItem(item)
        self.connection_items[connection.id] = item
        for other in self.connection_items.values():
            if {other.connection.source, other.connection.target} == {connection.source, connection.target}:
                other.update_path()
        return item

    def _block_at(self, pos: QPointF) -> BlockItem | None:
        return next((item for item in self.items(pos) if isinstance(item, BlockItem)), None)

    def mousePressEvent(self, event) -> None:
        if not self.read_only and event.button() == Qt.MouseButton.LeftButton:
            item = self._block_at(event.scenePos())
            if item is not None and item.handle_scene_rect().contains(event.scenePos()):
                self._drag_source = item
                start = item.mapToScene(item.handle_rect().center())
                pen = QPen(QColor(theme.ACCENT), 1.5, Qt.PenStyle.DashLine)
                self._drag_line = self.addLine(QLineF(start, start), pen)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_line is not None:
            line = self._drag_line.line()
            line.setP2(event.scenePos())
            self._drag_line.setLine(line)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_line is not None:
            self.removeItem(self._drag_line)
            self._drag_line = None
            source, self._drag_source = self._drag_source, None
            target = self._block_at(event.scenePos())
            if source is not None and target is not None:
                self.connect_blocks(source.block.id, target.block.id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        item = self._block_at(event.scenePos())
        if item is not None:
            self.block_activated.emit(item.block.component)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class CanvasView(QGraphicsView):
    def __init__(self, scene: DesignScene):
        super().__init__(scene)
        self.design_scene = scene
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        if scene.read_only:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            self.setAcceptDrops(True)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setSceneRect(-2000, -2000, 4000, 4000)
            self.centerOn(0, 0)

    def fit(self) -> None:
        bounds = self.design_scene.itemsBoundingRect()
        if bounds.isEmpty():
            return
        self.setSceneRect(bounds.adjusted(-16, -16, 16, 16))
        self.resetTransform()
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1:
            self.resetTransform()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.design_scene.read_only:
            self.fit()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(theme.BG))
        painter.setPen(QPen(QColor(theme.BORDER), 1.5))
        step = 24
        left = int(math.floor(rect.left() / step)) * step
        top = int(math.floor(rect.top() / step)) * step
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                painter.drawPoint(QPointF(x, y))
                y += step
            x += step

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        if self.design_scene.read_only or self.design_scene.design.blocks:
            return
        painter.setPen(QColor(theme.MUTED))
        painter.drawText(
            self.mapToScene(self.viewport().rect()).boundingRect(),
            Qt.AlignmentFlag.AlignCenter,
            "Drag a Component here to place a Block.\n"
            "Drag from the dot on a Block's right edge to another Block to connect them.\n"
            "A Connection points from caller to callee, or from sender to receiver.\n"
            "Select a Block or Connection to edit its properties; Delete removes it.",
        )

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.design_scene.delete_selected()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasFormat(MIME):
            return
        component_id = bytes(event.mimeData().data(MIME)).decode()
        self.design_scene.add_block(component_id, self.mapToScene(event.position().toPoint()))
        self.setFocus()
        event.acceptProposedAction()


class Palette(QListWidget):
    component_chosen = pyqtSignal(str)

    def __init__(self, library: Library):
        super().__init__()
        self.setDragEnabled(True)
        self.setFixedWidth(178)
        for page in sorted(library.components.values(), key=lambda p: p.name):
            item = QListWidgetItem(page.name)
            item.setData(Qt.ItemDataRole.UserRole, page.id)
            item.setToolTip("Drag onto the canvas, or double-click to place")
            self.addItem(item)
        self.itemDoubleClicked.connect(lambda item: self.component_chosen.emit(item.data(Qt.ItemDataRole.UserRole)))

    def startDrag(self, supported_actions) -> None:
        item = self.currentItem()
        if item is None:
            return
        mime = QMimeData()
        mime.setData(MIME, item.data(Qt.ItemDataRole.UserRole).encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class Inspector(QWidget):
    """Edits the properties of the selected Block or Connection in place."""

    edited = pyqtSignal(object)
    open_page = pyqtSignal(str)
    delete_requested = pyqtSignal()

    def __init__(self, library: Library):
        super().__init__()
        self.library = library
        self.setFixedWidth(262)
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(0, 0, 0, 0)
        self.body: QWidget | None = None
        self.show_target(None)

    def show_target(self, target: Block | Connection | None) -> None:
        if self.body is not None:
            self.outer.removeWidget(self.body)
            self.body.deleteLater()
        self.body = QWidget()
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        if isinstance(target, Block):
            self._block_form(layout, target)
        elif isinstance(target, Connection):
            self._connection_form(layout, target)
        else:
            layout.addWidget(label("Properties", "h3"))
            layout.addWidget(label("Select one Block or Connection to edit it.", "muted"))
        layout.addStretch(1)
        self.outer.addWidget(self.body)

    def _block_form(self, layout: QVBoxLayout, block: Block) -> None:
        page = self.library.components.get(block.component)
        layout.addWidget(label(f"Block: {page.name if page else block.component}", "h3"))
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow("Name", self._text(block, "name"))
        form.addRow("Technology", self._text(block, "technology", "e.g. Redis"))
        form.addRow("Instances", self._number(block, "instances"))
        form.addRow("Replication", self._number(block, "replication_factor"))
        key = self._text(block, "partition_key", "e.g. user_id")
        key.setEnabled(block.partitioning != "none")
        partitioning = self._choice(block, "partitioning", PARTITIONING)
        partitioning.currentTextChanged.connect(lambda value: key.setEnabled(value != "none"))
        form.addRow("Partitioning", partitioning)
        form.addRow("Partition key", key)
        for extra in (page.extras if page else ()):
            form.addRow(extra.label, self._extra(block, extra.key, extra.options))
        layout.addLayout(form)
        note = QPlainTextEdit(block.note)
        note.setPlaceholderText("Note")
        note.setFixedHeight(64)
        note.textChanged.connect(lambda: self._set(block, "note", note.toPlainText()))
        layout.addWidget(note)
        buttons = QHBoxLayout()
        open_page = QPushButton("Open Page")
        open_page.clicked.connect(lambda: self.open_page.emit(block.component))
        delete = QPushButton("Delete")
        delete.clicked.connect(self.delete_requested.emit)
        buttons.addWidget(open_page)
        buttons.addWidget(delete)
        layout.addLayout(buttons)

    def _connection_form(self, layout: QVBoxLayout, connection: Connection) -> None:
        layout.addWidget(label("Connection", "h3"))
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow("Mode", self._choice(connection, "mode", MODES))
        protocol = self._choice(connection, "protocol", PROTOCOLS, editable=True)
        form.addRow("Protocol", protocol)
        form.addRow("Path", self._choice(connection, "path", PATHS))
        form.addRow("Label", self._text(connection, "label"))
        layout.addLayout(form)
        layout.addWidget(label("Solid line: sync. Dashed line: async.", "muted"))
        delete = QPushButton("Delete")
        delete.clicked.connect(self.delete_requested.emit)
        layout.addWidget(delete)

    def _set(self, target, attribute: str, value) -> None:
        setattr(target, attribute, value)
        self.edited.emit(target)

    def _text(self, target, attribute: str, placeholder: str = "") -> QLineEdit:
        edit = QLineEdit(getattr(target, attribute))
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(lambda text: self._set(target, attribute, text))
        return edit

    def _number(self, target, attribute: str) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(1, 100000)
        spin.setValue(getattr(target, attribute))
        spin.valueChanged.connect(lambda value: self._set(target, attribute, value))
        return spin

    def _choice(self, target, attribute: str, options, editable: bool = False) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(editable)
        combo.addItems(options)
        current = getattr(target, attribute)
        if combo.findText(current) < 0:
            combo.addItem(current)
        combo.setCurrentText(current)
        combo.currentTextChanged.connect(lambda value: self._set(target, attribute, value))
        return combo

    def _extra(self, block: Block, key: str, options) -> QComboBox:
        combo = QComboBox()
        combo.addItems(["", *options])
        combo.setCurrentText(block.extras.get(key, ""))

        def store(value: str) -> None:
            if value:
                block.extras[key] = value
            else:
                block.extras.pop(key, None)
            self.edited.emit(block)

        combo.currentTextChanged.connect(store)
        return combo


class CanvasEditor(QWidget):
    design_changed = pyqtSignal()
    open_page = pyqtSignal(str)

    def __init__(self, library: Library):
        super().__init__()
        self.scene = DesignScene(library)
        self.view = CanvasView(self.scene)
        self.palette = Palette(library)
        self.inspector = Inspector(library)

        left = QVBoxLayout()
        left.setSpacing(6)
        left.addWidget(label("Components", "h3"))
        left.addWidget(self.palette, 1)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(left)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.inspector)

        self.scene.selectionChanged.connect(self._selection_changed)
        self.scene.design_changed.connect(self.design_changed.emit)
        self.scene.block_activated.connect(self.open_page.emit)
        self.inspector.edited.connect(self.scene.object_edited)
        self.inspector.open_page.connect(self.open_page.emit)
        self.inspector.delete_requested.connect(self.scene.delete_selected)
        self.palette.component_chosen.connect(self._place_in_view)

    @property
    def design(self) -> Design:
        return self.scene.design

    def _selection_changed(self) -> None:
        # Qt emits selectionChanged from the scene's destructor, after the Python side is gone.
        if sip.isdeleted(self.scene) or sip.isdeleted(self.inspector):
            return
        self.inspector.show_target(self.scene.selected_object())

    def _place_in_view(self, component_id: str) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        jitter = 18 * (len(self.design.blocks) % 6)
        self.scene.add_block(component_id, center + QPointF(jitter, jitter))
