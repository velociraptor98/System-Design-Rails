"""Report every Citation URL that no longer resolves.

Run from the repository root:  python scripts/check_links.py
Exits non-zero if any URL fails. A URL that answers 403 is reported as blocked,
not broken: some hosts refuse scripted requests but open in a browser.
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sysdesignhelper.content import load_library  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (sysdesignhelper link check)"}


def status_of(url: str) -> int | str:
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except (urllib.error.URLError, TimeoutError) as error:
        return str(error)


def main() -> int:
    library = load_library()
    broken = 0
    for key, citation in sorted(library.sources.items()):
        status = status_of(citation.url)
        if status == 200:
            verdict = "ok"
        elif status in (401, 403):
            verdict = "blocked (open it in a browser to confirm)"
        else:
            verdict = f"BROKEN ({status})"
            broken += 1
        flag = "" if citation.retrieved else "  [not retrieved]"
        print(f"{verdict:45} {key}{flag}\n{'':45} {citation.url}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
