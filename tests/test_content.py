import json
from pathlib import Path

import pytest

from sysdesignhelper.checks import run_checks
from sysdesignhelper.content import REAL_SYSTEM, ContentError, load_library
from sysdesignhelper.design import Design


def all_claims(library):
    for page in [*library.components.values(), *library.mechanisms.values()]:
        for section in page.sections:
            yield from section.claims
        for prompt in page.recall:
            yield from prompt.answer
    for question in library.questions.values():
        answers = [question.api, question.data_model, question.architecture.answer]
        answers += [dive.answer for dive in question.deep_dives]
        for answer in answers:
            yield from answer.key_points
        for check in question.architecture.checks:
            yield check.rationale


def test_every_claim_is_cited_or_marked_synthesis(library):
    claims = list(all_claims(library))
    assert claims
    for claim in claims:
        assert claim.synthesis != bool(claim.citations), claim.text


def test_real_system_answers_contain_no_synthesis(library):
    for question in library.questions.values():
        answers = [question.api, question.data_model, question.architecture.answer]
        answers += [dive.answer for dive in question.deep_dives]
        for answer in answers:
            if answer.kind == REAL_SYSTEM:
                assert not any(point.synthesis for point in answer.key_points)


def test_every_source_is_cited_somewhere(library):
    cited = {citation.url for claim in all_claims(library) for citation in claim.citations}
    assert cited == {source.url for source in library.sources.values()}


def test_every_page_has_recall_prompts(library):
    for page in [*library.components.values(), *library.mechanisms.values()]:
        assert page.recall, page.id


def test_reference_design_passes_its_own_checks(library):
    for question in library.questions.values():
        results = run_checks(question.architecture.checks, question.architecture.design)
        failed = [result.check.id for result in results if not result.passed]
        assert not failed, f"{question.id}: {failed}"


def test_empty_design_fails_every_check(library):
    for question in library.questions.values():
        results = run_checks(question.architecture.checks, Design())
        assert not any(result.passed for result in results), question.id


def test_each_question_has_two_to_four_deep_dives(library):
    for question in library.questions.values():
        assert 2 <= len(question.deep_dives) <= 4, question.id


def write_minimal_content(root: Path, claim: dict):
    (root / "components").mkdir()
    (root / "mechanisms").mkdir()
    (root / "questions").mkdir()
    (root / "sources.json").write_text(json.dumps({"src": {"url": "https://example.org/a", "retrieved": False}}))
    page = {
        "id": "thing", "name": "Thing",
        "sections": [{"heading": "H", "claims": [claim]}],
        "recall": [{"prompt": "P?", "answer": [{"text": "A", "cite": ["src"]}]}],
    }
    (root / "mechanisms" / "thing.json").write_text(json.dumps(page))


def test_uncited_claim_is_rejected(tmp_path):
    write_minimal_content(tmp_path, {"text": "No source for this."})
    with pytest.raises(ContentError, match="no citation"):
        load_library(tmp_path)


def test_synthesis_is_rejected_on_a_page(tmp_path):
    write_minimal_content(tmp_path, {"text": "My own view.", "synthesis": True})
    with pytest.raises(ContentError, match="synthesis is only allowed"):
        load_library(tmp_path)


def test_unknown_source_is_rejected(tmp_path):
    write_minimal_content(tmp_path, {"text": "Cited to nothing.", "cite": ["missing"]})
    with pytest.raises(ContentError, match="unknown source"):
        load_library(tmp_path)


def test_not_retrieved_citation_is_kept(tmp_path):
    write_minimal_content(tmp_path, {"text": "Source was not opened.", "cite": ["src"]})
    library = load_library(tmp_path)
    claim = library.mechanisms["thing"].sections[0].claims[0]
    assert claim.citations[0].retrieved is False
