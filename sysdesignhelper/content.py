from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .design import Design

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

REAL_SYSTEM = "real-system"
SYNTHESIZED = "synthesized"
CATEGORIES = ("general", "trading")


class ContentError(Exception):
    pass


@dataclass(frozen=True)
class Citation:
    url: str
    retrieved: bool


@dataclass(frozen=True)
class Claim:
    text: str
    citations: tuple[Citation, ...] = ()
    synthesis: bool = False


@dataclass(frozen=True)
class Section:
    heading: str
    claims: tuple[Claim, ...]


@dataclass(frozen=True)
class RecallPrompt:
    prompt: str
    answer: tuple[Claim, ...]
    page_id: str = ""


@dataclass(frozen=True)
class ExtraField:
    key: str
    label: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class Page:
    id: str
    kind: str
    name: str
    sections: tuple[Section, ...]
    recall: tuple[RecallPrompt, ...]
    mechanisms: tuple[str, ...] = ()
    extras: tuple[ExtraField, ...] = ()


@dataclass(frozen=True)
class CompanyTag:
    company: str
    reports: tuple[str, ...]


@dataclass(frozen=True)
class Estimate:
    label: str
    working: str
    result: str


@dataclass(frozen=True)
class Scope:
    functional: tuple[str, ...]
    non_functional: tuple[str, ...]
    assumptions: tuple[str, ...]
    estimates: tuple[Estimate, ...]


@dataclass(frozen=True)
class StageAnswer:
    kind: str
    system: str
    key_points: tuple[Claim, ...]


@dataclass(frozen=True)
class DeepDive:
    prompt: str
    answer: StageAnswer
    pages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    miss: str
    rule: dict
    rationale: Claim


@dataclass(frozen=True)
class Architecture:
    answer: StageAnswer
    design: Design
    checks: tuple[Check, ...]


@dataclass(frozen=True)
class Question:
    id: str
    title: str
    category: str
    prompt: str
    company_tags: tuple[CompanyTag, ...]
    scope: Scope
    api: StageAnswer
    data_model: StageAnswer
    architecture: Architecture
    deep_dives: tuple[DeepDive, ...]


@dataclass
class Library:
    sources: dict[str, Citation] = field(default_factory=dict)
    components: dict[str, Page] = field(default_factory=dict)
    mechanisms: dict[str, Page] = field(default_factory=dict)
    questions: dict[str, Question] = field(default_factory=dict)

    def page(self, page_id: str) -> Page | None:
        return self.components.get(page_id) or self.mechanisms.get(page_id)

    def companies(self) -> list[str]:
        return sorted({tag.company for q in self.questions.values() for tag in q.company_tags})


def load_library(content_dir: Path = CONTENT_DIR) -> Library:
    return _Loader(content_dir).load()


class _Loader:
    def __init__(self, content_dir: Path):
        self.dir = content_dir
        self.library = Library()
        self.where = ""

    def load(self) -> Library:
        self.where = "sources.yaml"
        for key, raw in self._read(self.dir / "sources.yaml").items():
            self.library.sources[key] = Citation(url=raw["url"], retrieved=bool(raw["retrieved"]))

        for kind, target in (("mechanism", self.library.mechanisms), ("component", self.library.components)):
            for path in sorted((self.dir / f"{kind}s").glob("*.yaml")):
                self.where = f"{kind}s/{path.name}"
                page = self._page(self._read(path), kind)
                target[page.id] = page

        for page in self.library.components.values():
            for mechanism in page.mechanisms:
                if mechanism not in self.library.mechanisms:
                    raise ContentError(f"components/{page.id}.yaml: unknown mechanism {mechanism!r}")

        for path in sorted((self.dir / "questions").glob("*.yaml")):
            self.where = f"questions/{path.name}"
            question = self._question(self._read(path))
            self.library.questions[question.id] = question
        return self.library

    def _read(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _fail(self, message: str):
        raise ContentError(f"{self.where}: {message}")

    def _claim(self, raw: dict, allow_synthesis: bool = False) -> Claim:
        text = " ".join(str(raw["text"]).split())
        synthesis = bool(raw.get("synthesis", False))
        keys = raw.get("cite", [])
        if synthesis:
            if not allow_synthesis:
                self._fail(f"synthesis is only allowed in a synthesized answer: {text!r}")
            if keys:
                self._fail(f"a synthesis claim cannot carry citations: {text!r}")
            return Claim(text=text, synthesis=True)
        if not keys:
            self._fail(f"claim has no citation: {text!r}")
        citations = []
        for key in keys:
            if key not in self.library.sources:
                self._fail(f"unknown source {key!r}")
            citations.append(self.library.sources[key])
        return Claim(text=text, citations=tuple(citations))

    def _claims(self, raw_list, allow_synthesis: bool = False) -> tuple[Claim, ...]:
        claims = tuple(self._claim(raw, allow_synthesis) for raw in raw_list or [])
        if not claims:
            self._fail("expected at least one claim")
        return claims

    def _page(self, raw: dict, kind: str) -> Page:
        page_id = raw["id"]
        return Page(
            id=page_id,
            kind=kind,
            name=raw["name"],
            sections=tuple(
                Section(heading=s["heading"], claims=self._claims(s["claims"])) for s in raw["sections"]
            ),
            recall=tuple(
                RecallPrompt(prompt=r["prompt"], answer=self._claims(r["answer"]), page_id=page_id)
                for r in raw["recall"]
            ),
            mechanisms=tuple(raw.get("mechanisms", [])),
            extras=tuple(
                ExtraField(key=e["key"], label=e["label"], options=tuple(e["options"]))
                for e in raw.get("extras", [])
            ),
        )

    def _answer(self, raw: dict, points_key: str = "key_points") -> StageAnswer:
        kind = raw["kind"]
        if kind not in (REAL_SYSTEM, SYNTHESIZED):
            self._fail(f"unknown answer kind {kind!r}")
        system = raw.get("system", "")
        if kind == REAL_SYSTEM and not system:
            self._fail("a real-system answer must name its system")
        return StageAnswer(
            kind=kind,
            system=system,
            key_points=self._claims(raw[points_key], allow_synthesis=kind == SYNTHESIZED),
        )

    def _question(self, raw: dict) -> Question:
        if raw["category"] not in CATEGORIES:
            self._fail(f"unknown category {raw['category']!r}")
        scope = raw["scope"]
        architecture = raw["architecture"]
        design = Design.from_dict(architecture["design"])
        for block in design.blocks:
            if block.component not in self.library.components:
                self._fail(f"reference design uses unknown component {block.component!r}")
        deep_dives = []
        for dive in raw["deep_dives"]:
            for page_id in dive.get("pages", []):
                if self.library.page(page_id) is None:
                    self._fail(f"deep dive links to unknown page {page_id!r}")
            deep_dives.append(DeepDive(
                prompt=dive["prompt"],
                answer=self._answer(dive),
                pages=tuple(dive.get("pages", [])),
            ))
        return Question(
            id=raw["id"],
            title=raw["title"],
            category=raw["category"],
            prompt=" ".join(raw["prompt"].split()),
            company_tags=tuple(
                CompanyTag(company=t["company"], reports=tuple(t["reports"]))
                for t in raw.get("company_tags", [])
            ),
            scope=Scope(
                functional=tuple(scope["functional"]),
                non_functional=tuple(scope["non_functional"]),
                assumptions=tuple(scope["assumptions"]),
                estimates=tuple(Estimate(**e) for e in scope["estimates"]),
            ),
            api=self._answer(raw["api"]),
            data_model=self._answer(raw["data_model"]),
            architecture=Architecture(
                answer=self._answer(architecture, points_key="notes"),
                design=design,
                checks=tuple(
                    Check(id=c["id"], title=c["title"], miss=c["miss"], rule=c["rule"],
                          rationale=self._claim(c["rationale"]))
                    for c in architecture["checks"]
                ),
            ),
            deep_dives=tuple(deep_dives),
        )
