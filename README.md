# System Design Practice

A desktop trainer for system design interviews. You attempt a Question stage by stage, build the
architecture as a Design on a drag-and-drop Canvas, and then reveal a Reference answer in which
every factual claim links to a primary source.

Nothing you type or draw is saved. A Practice session lives in memory and is gone when you close it.

## Run

Requires Python 3.12 or newer. Developed and tested on macOS only.

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m sysdesignhelper
```

## How it works

- **Questions**: each has six Stages: Requirements, Estimates, API, Data model, Architecture and
  Deep dives. Write your answer, then reveal the Reference answer and tick the Key points you covered.
- **Canvas**: drag Components onto the Canvas to place Blocks, drag from the dot on a Block's right
  edge to another Block to connect them, and select a Block or Connection to set its properties.
  On reveal, the Question's Checks run against your Design and re-run as you edit.
- **Pages**: reference material on Components and the Mechanisms inside them, each with Recall
  prompts you can drill from one Page or shuffled across several.
- **Sandbox**: a Canvas with no Question attached.

## Correctness rules

- Every factual claim cites a primary source: a paper, an RFC, official product documentation, or a
  post or talk by the team that built the system. A Citation is the source's URL.
- A source that could not be opened when the claim was written is shown as "not retrieved".
- A Real-system answer reports how a real company published that it built the system. A Synthesized
  answer is a last resort, carries a disclaimer, and shows its uncited judgement in italics.
- A Question's Scope (its requirements and scale assumptions) defines the Question and carries no Citation.
- Company tags come from LeetCode candidate reports and are shown as reported, not verified.

`CONTEXT.md` defines the vocabulary used here and in the code. `docs/adr/` records the decisions
behind these rules.

## Content

All content is plain YAML under `content/`, separate from the code:

- `sources.yaml`: every cited URL, and whether it was retrieved.
- `components/` and `mechanisms/`: one Page per file.
- `questions/`: one Question per file, including its reference Design and its Checks. The rule
  vocabulary for Checks is documented at the top of `sysdesignhelper/checks.py`.

The app refuses to load content in which a claim has no Citation.

## Tests

```sh
.venv/bin/python -m pytest
.venv/bin/python scripts/check_links.py   # confirms every cited URL still resolves
```

## Licence

GPL-3.0-only, which PyQt6 requires of a public project. See `docs/adr/0001-pyqt6-and-gpl.md`.
