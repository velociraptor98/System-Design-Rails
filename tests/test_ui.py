import copy

import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QLineEdit

from sysdesignhelper.app import apply_theme
from sysdesignhelper.ui.main_window import AREAS, MainWindow
from sysdesignhelper.ui.pages import PAGE_ID
from sysdesignhelper.ui.session import STAGES


@pytest.fixture
def window(qtbot, qapp, library):
    apply_theme(qapp)
    main = MainWindow(library)
    main.confirm = lambda parent: True
    main.questions.confirm = lambda parent: True
    qtbot.addWidget(main)
    main.show()
    return main


@pytest.fixture
def session(window):
    window.questions.start_session("url-shortener")
    return window.questions.session


def test_window_has_three_areas(window):
    assert [button.text() for button in window.nav.buttons()] == list(AREAS)
    window.show_area(2)
    assert window.stack.currentWidget() is window.sandbox


def test_question_filters(window):
    view = window.questions
    assert len(view.visible_questions()) == len(view.library.questions)
    view.category.setCurrentIndex(view.category.findData("trading"))
    assert {q.category for q in view.visible_questions()} == {"trading"}
    view.category.setCurrentIndex(0)
    view.company.setCurrentIndex(view.company.findData("Goldman Sachs"))
    tagged = view.visible_questions()
    assert tagged and all(any(t.company == "Goldman Sachs" for t in q.company_tags) for q in tagged)


def test_session_has_six_stages_and_reveals(session):
    assert session.stack.count() == len(STAGES) == 6
    for box in session.attempts:
        assert box.revealed is None
        box.reveal()
        assert box.revealed is not None
    assert len(session.attempts) == 4 + len(session.question.deep_dives)


def test_typing_counts_as_work_and_leaving_asks(window, session):
    assert not session.has_work()
    session.attempts[0].editor.setPlainText("shorten, redirect")
    assert session.has_work()
    window.questions.confirm = lambda parent: False
    window.questions.close_session()
    assert window.questions.session is session
    window.questions.confirm = lambda parent: True
    window.questions.close_session()
    assert window.questions.session is None


def test_checks_follow_the_design(session):
    stage = session.architecture
    scene = stage.editor.scene
    service = scene.add_block("service", QPointF(0, 0))
    database = scene.add_block("database", QPointF(300, 0))
    scene.connect_blocks(service.id, database.id)
    stage.reveal()
    total = len(session.question.architecture.checks)
    assert stage.tabs.tabText(0) == f"Checks: 0 of {total} hold"

    database.replication_factor = 3
    scene.object_edited(database)
    assert stage.tabs.tabText(0) == f"Checks: 1 of {total} hold"

    scene.load(copy.deepcopy(session.question.architecture.design))
    assert stage.tabs.tabText(0) == f"Checks: {total} of {total} hold"


def test_inspector_edits_the_selected_block(session):
    editor = session.architecture.editor
    block = editor.scene.add_block("cache", QPointF(0, 0))
    assert editor.scene.selected_object() is block
    name = editor.inspector.findChildren(QLineEdit)[0]
    name.setText("Hot links")
    assert block.name == "Hot links"


def test_cannot_connect_a_block_to_itself_or_twice(session):
    scene = session.architecture.editor.scene
    a = scene.add_block("client", QPointF(0, 0))
    b = scene.add_block("service", QPointF(300, 0))
    assert scene.connect_blocks(a.id, a.id) is None
    assert scene.connect_blocks(a.id, b.id) is not None
    assert scene.connect_blocks(a.id, b.id) is None
    assert scene.connect_blocks(b.id, a.id) is not None


def test_deleting_a_block_removes_its_connections(session):
    scene = session.architecture.editor.scene
    a = scene.add_block("client", QPointF(0, 0))
    b = scene.add_block("service", QPointF(300, 0))
    scene.connect_blocks(a.id, b.id)
    scene.clearSelection()
    scene.block_items[b.id].setSelected(True)
    scene.delete_selected()
    assert [block.id for block in scene.design.blocks] == [a.id]
    assert scene.design.connections == []


def test_opening_a_page_from_a_session_keeps_the_session(window, session):
    session.open_page.emit("cache")
    assert window.stack.currentWidget() is window.pages
    assert [page.id for page in window.pages.selected_pages()] == ["cache"]
    assert window.questions.session is session


def test_recall_drill_runs_across_selected_pages(window, library):
    pages = window.pages
    pages.show_page("cache")
    for row in range(pages.listing.count()):
        item = pages.listing.item(row)
        if item.data(PAGE_ID) == "consistent-hashing":
            item.setSelected(True)
    expected = len(library.page("cache").recall) + len(library.page("consistent-hashing").recall)
    pages.start_drill()
    drill = pages.drill
    assert len(drill.prompts) == expected
    for _ in range(expected):
        drill.reveal()
        drill.next()
    assert pages.drill is None


def test_quit_is_refused_while_there_is_work(window):
    window.sandbox.editor.scene.add_block("client", QPointF(0, 0))
    window.confirm = lambda parent: False
    event = QCloseEvent()
    window.closeEvent(event)
    assert not event.isAccepted()
    window.confirm = lambda parent: True
    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted()
